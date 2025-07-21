import os
import shutil
import re
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import zipfile
import sys

from fastapi import FastAPI, HTTPException, Depends, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import aiofiles
from loguru import logger

# 加载环境变量
load_dotenv()

# 配置loguru日志
logger.remove()  # 移除默认处理器
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

app = FastAPI(title="HTML Fast Deploy", description="HTML 快速部署系统")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 安全配置
security = HTTPBasic()

# 模板配置
templates = Jinja2Templates(directory="templates")

# 添加自定义过滤器
def datetime_filter(timestamp):
    """将时间戳转换为可读的日期时间格式"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

templates.env.filters["datetime"] = datetime_filter

# 静态文件配置
app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建必要的目录
APPS_DIR = Path("apps")
APPS_DIR.mkdir(exist_ok=True)

# 从环境变量获取用户配置
def get_users_from_env():
    """从环境变量获取用户配置"""
    users = {}
    i = 1
    while True:
        username = os.getenv(f"USER_{i}_NAME")
        password = os.getenv(f"USER_{i}_PASSWORD")
        if not username or not password:
            break
        users[username] = password
        i += 1
    
    # 如果没有配置用户，使用默认配置
    if not users:
        users = {
            "admin": "admin123"
        }
    
    return users

USERS = get_users_from_env()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """验证用户凭据"""
    if credentials.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not USERS[credentials.username] == credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

def is_valid_app_name(app_name: str) -> bool:
    """验证应用名称是否合法（只能使用英文、数字、下划线、连字符）"""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', app_name))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - 重定向到登录"""
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    """登录验证"""
    username = verify_credentials(credentials)
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理页面"""
    # 获取所有应用
    apps = []
    if APPS_DIR.exists():
        # 查找单个HTML文件应用
        for file_path in APPS_DIR.glob("*.html"):
            app_name = file_path.stem
            apps.append({
                "name": app_name,
                "filename": file_path.name,
                "created_time": file_path.stat().st_ctime,
                "type": "single_file"
            })
        
        # 查找目录形式的应用
        for dir_path in APPS_DIR.iterdir():
            if dir_path.is_dir() and is_valid_app_name(dir_path.name):
                index_path = dir_path / "index.html"
                if index_path.exists():
                    apps.append({
                        "name": dir_path.name,
                        "filename": "index.html",
                        "created_time": index_path.stat().st_ctime,
                        "type": "directory"
                    })
    
    # 按创建时间排序
    apps.sort(key=lambda x: x["created_time"], reverse=True)
    logger.debug(f"应用列表: {apps}")
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "apps": apps,
        "username": "admin"  # 默认用户名，实际会通过 JavaScript 获取
    })

@app.post("/admin/apps")
async def create_app(
    app_name: str = Form(...),
    html_file: UploadFile = File(...),
    username: str = Depends(verify_credentials)):
    """创建应用"""
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
    # 检查文件类型
    if html_file.filename.endswith('.html'):
        # 单个HTML文件
        app_file_path = APPS_DIR / f"{app_name}.html"
        
        # 保存文件
        async with aiofiles.open(app_file_path, 'wb') as f:
            content = await html_file.read()
            await f.write(content)
            
    elif html_file.filename.endswith('.zip'):
        # ZIP文件，包含静态资源
        app_dir = APPS_DIR / app_name
        app_dir.mkdir(exist_ok=True)
        
        # 保存ZIP文件
        zip_path = app_dir / "app.zip"
        async with aiofiles.open(zip_path, 'wb') as f:
            content = await html_file.read()
            await f.write(content)
        
        # 解压ZIP文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(app_dir)
        
        # 删除ZIP文件
        zip_path.unlink()
        
        # 检查是否有index.html
        index_path = app_dir / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=400, detail="ZIP文件中必须包含index.html文件")
            
    else:
        raise HTTPException(status_code=400, detail="只能上传HTML文件或ZIP文件")
    
    return {"message": "应用创建成功", "app_name": app_name}

@app.delete("/admin/apps/{app_name}")
async def delete_app(app_name: str, username: str = Depends(verify_credentials)):
    """删除应用"""
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
    # 检查是否是目录形式的应用
    app_dir = APPS_DIR / app_name
    if app_dir.exists() and app_dir.is_dir():
        # 删除整个目录
        shutil.rmtree(app_dir)
    else:
        # 单个HTML文件
        app_file_path = APPS_DIR / f"{app_name}.html"
        if not app_file_path.exists():
            raise HTTPException(status_code=404, detail="应用不存在")
        app_file_path.unlink()
    
    return {"message": "应用删除成功"}

@app.put("/admin/apps/{app_name}")
async def update_app(
    app_name: str,
    html_file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """更新应用"""
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
    # 检查应用是否存在
    app_dir = APPS_DIR / app_name
    app_file_path = APPS_DIR / f"{app_name}.html"
    
    if not app_dir.exists() and not app_file_path.exists():
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 检查文件类型
    if html_file.filename.endswith('.html'):
        # 更新为单个HTML文件
        # 如果原来是目录，先删除
        if app_dir.exists() and app_dir.is_dir():
            shutil.rmtree(app_dir)
        
        # 保存新的HTML文件
        async with aiofiles.open(app_file_path, 'wb') as f:
            content = await html_file.read()
            await f.write(content)
            
    elif html_file.filename.endswith('.zip'):
        # 更新为ZIP文件（包含静态资源）
        # 如果原来是单个文件，先删除
        if app_file_path.exists():
            app_file_path.unlink()
        
        # 重新创建目录
        if app_dir.exists():
            shutil.rmtree(app_dir)
        app_dir.mkdir(exist_ok=True)
        
        # 保存ZIP文件
        zip_path = app_dir / "app.zip"
        async with aiofiles.open(zip_path, 'wb') as f:
            content = await html_file.read()
            await f.write(content)
        
        # 解压ZIP文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(app_dir)
        
        # 删除ZIP文件
        zip_path.unlink()
        
        # 检查是否有index.html
        index_path = app_dir / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=400, detail="ZIP文件中必须包含index.html文件")
            
    else:
        raise HTTPException(status_code=400, detail="只能上传HTML文件或ZIP文件")
    
    return {"message": "应用更新成功"}

@app.get("/apps/{path:path}")
async def serve_app_or_static(path: str, request: Request):
    """提供应用页面或静态资源"""
    logger.debug(f"请求路径: {path}")
    
    # 检查是否是静态资源请求（直接请求文件）
    if "." in path and not path.endswith('.html'):
        logger.info(f"静态资源请求: {path}")
        
        # 从Referer头中获取应用名称
        referer = request.headers.get("referer", "")
        app_name = None
        
        logger.debug(f"Referer头: {referer}")
        
        if referer:
            # 从Referer中提取应用名称
            import re
            match = re.search(r'/apps/([^/]+)', referer)
            if match:
                app_name = match.group(1)
                logger.debug(f"从Referer提取的应用名称: {app_name}")
            else:
                logger.warning(f"无法从Referer中提取应用名称: {referer}")
                # 尝试其他模式
                match = re.search(r'/apps/([^/?]+)', referer)
                if match:
                    app_name = match.group(1)
                    logger.debug(f"使用备用模式提取的应用名称: {app_name}")
        else:
            logger.warning("没有Referer头")
        
        # 如果从Referer获取到应用名称，在该应用中查找
        if app_name and is_valid_app_name(app_name):
            app_dir = APPS_DIR / app_name
            if app_dir.exists() and app_dir.is_dir():
                # 从path中提取文件名（去掉应用名称前缀）
                if path.startswith(f"{app_name}/"):
                    file_path = path[len(app_name)+1:]  # 去掉 "app_name/" 前缀
                else:
                    file_path = path  # 如果没有前缀，直接使用path
                
                static_path = app_dir / file_path
                logger.debug(f"在应用 {app_name} 中检查路径: {static_path}")
                if static_path.exists() and static_path.is_file():
                    logger.info(f"找到静态资源: {static_path}")
                    return await serve_static_file(static_path, file_path)
                else:
                    logger.warning(f"未找到静态资源: {static_path}")
            else:
                logger.warning(f"应用目录不存在: {app_dir}")
        else:
            logger.warning(f"应用名称无效或为空: {app_name}")
        
        # 如果没有Referer或找不到，返回404（不再混用不同应用的资源）
        logger.error(f"未找到静态资源或无法确定应用上下文: {path}")
        raise HTTPException(status_code=404, detail="静态资源不存在或无法确定应用上下文")
    
    # 检查是否是应用请求
    app_name = path.split('/')[0] if '/' in path else path
    logger.debug(f"应用名称: {app_name}")
    
    # 验证应用名称
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
    # 检查是否是目录形式的应用
    app_dir = APPS_DIR / app_name
    if app_dir.exists() and app_dir.is_dir():
        # 如果是根路径或index.html，返回index.html
        if path == app_name or path == f"{app_name}/" or path == f"{app_name}/index.html":
            logger.info(f"匹配到应用根路径: {path}")
            index_path = app_dir / "index.html"
            logger.debug(f"查找index.html: {index_path}")
            if index_path.exists():
                logger.info(f"找到index.html文件")
                async with aiofiles.open(index_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # 替换以/开头的相对路径为以./开头的相对路径
                # 使用正则表达式匹配以/开头但不是完整URL的路径
                import re
                
                def replace_absolute_paths(path):
                    """替换绝对路径为相对路径"""
                    # 如果是以http或https开头的完整URL，保持不变
                    if path.startswith(('http://', 'https://', '//')):
                        return path
                    # 如果是以/开头的相对路径，替换为以./开头
                    if path.startswith('/'):
                        return './' + path[1:]
                    return path
                
                # 匹配HTML中的各种属性中的路径
                # 匹配 src="..." 或 href="..." 或 data-src="..." 等属性中的路径
                content = re.sub(r'(["\'])(/[^"\']*?)(["\'])', 
                               lambda m: m.group(1) + replace_absolute_paths(m.group(2)) + m.group(3), 
                               content)
                
                # 匹配CSS中的url()路径
                content = re.sub(r'url\((["\']?)(/[^"\')]*?)(["\']?)\)', 
                               lambda m: 'url(' + m.group(1) + replace_absolute_paths(m.group(2)) + m.group(3) + ')', 
                               content)
                
                # 图片
                content = re.sub(r'src="([^"]+\.(jpg|jpeg|png|gif|svg|ico|woff|woff2|ttf|eot))"', 
                               lambda m: f'src="{replace_absolute_paths(m.group(1))}"', 
                               content)
                
                logger.info(f"返回处理后的HTML内容")
                
                return HTMLResponse(content=content)
            else:
                logger.error(f"未找到index.html文件: {index_path}")
                raise HTTPException(status_code=404, detail="应用目录中未找到index.html文件")
        else:
            logger.debug(f"路径不匹配应用根路径: {path} != {app_name} or {app_name}/ or {app_name}/index.html")
        
        # 检查是否是应用内的静态资源
        if path.startswith(f"{app_name}/"):
            static_path = app_dir / path[len(app_name)+1:]
            if static_path.exists() and static_path.is_file():
                return await serve_static_file(static_path, path[len(app_name)+1:])
    
    # 单个HTML文件形式
    app_file_path = APPS_DIR / f"{app_name}.html"
    if not app_file_path.exists():
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 读取并返回 HTML 文件内容
    logger.info(f"返回单个HTML文件: {app_file_path}")
    async with aiofiles.open(app_file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    
    return HTMLResponse(content=content)

async def serve_static_file(file_path: Path, path: str):
    """提供静态文件"""
    # 检查文件类型
    content_type = "application/octet-stream"
    if path.endswith('.css'):
        content_type = "text/css"
    elif path.endswith('.js'):
        content_type = "application/javascript"
    elif path.endswith('.png'):
        content_type = "image/png"
    elif path.endswith('.jpg') or path.endswith('.jpeg'):
        content_type = "image/jpeg"
    elif path.endswith('.gif'):
        content_type = "image/gif"
    elif path.endswith('.svg'):
        content_type = "image/svg+xml"
    elif path.endswith('.ico'):
        content_type = "image/x-icon"
    elif path.endswith('.woff'):
        content_type = "font/woff"
    elif path.endswith('.woff2'):
        content_type = "font/woff2"
    elif path.endswith('.ttf'):
        content_type = "font/ttf"
    elif path.endswith('.eot'):
        content_type = "font/eot"
    
    # 读取文件内容
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    
    from fastapi.responses import Response
    return Response(content=content, media_type=content_type)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 