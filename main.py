import os
import shutil
import re
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import uvicorn
from dotenv import load_dotenv
import aiofiles

# 加载环境变量
load_dotenv()

app = FastAPI(title="HTML Fast Deploy", description="HTML 快速部署系统")

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
        for file_path in APPS_DIR.glob("*.html"):
            app_name = file_path.stem
            apps.append({
                "name": app_name,
                "filename": file_path.name,
                "created_time": file_path.stat().st_ctime
            })
    
    # 按创建时间排序
    apps.sort(key=lambda x: x["created_time"], reverse=True)
    print(apps)
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "apps": apps,
        "username": "admin"  # 默认用户名，实际会通过 JavaScript 获取
    })

@app.post("/admin/apps")
async def create_app(
    app_name: str = Form(...),
    html_file: UploadFile = File(...),
    username: str = Depends(verify_credentials)
):
    """创建应用"""
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
    if not html_file.filename.endswith('.html'):
        raise HTTPException(status_code=400, detail="只能上传 HTML 文件")
    
    app_file_path = APPS_DIR / f"{app_name}.html"
    
    # 保存文件
    async with aiofiles.open(app_file_path, 'wb') as f:
        content = await html_file.read()
        await f.write(content)
    
    return {"message": "应用创建成功", "app_name": app_name}

@app.delete("/admin/apps/{app_name}")
async def delete_app(app_name: str, username: str = Depends(verify_credentials)):
    """删除应用"""
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
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
    
    if not html_file.filename.endswith('.html'):
        raise HTTPException(status_code=400, detail="只能上传 HTML 文件")
    
    app_file_path = APPS_DIR / f"{app_name}.html"
    
    if not app_file_path.exists():
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 保存文件
    async with aiofiles.open(app_file_path, 'wb') as f:
        content = await html_file.read()
        await f.write(content)
    
    return {"message": "应用更新成功"}

@app.get("/apps/{app_name}", response_class=HTMLResponse)
async def serve_app(app_name: str, request: Request):
    """提供应用页面"""
    if not is_valid_app_name(app_name):
        raise HTTPException(status_code=400, detail="应用名称只能包含英文、数字、下划线和连字符")
    
    app_file_path = APPS_DIR / f"{app_name}.html"
    
    if not app_file_path.exists():
        raise HTTPException(status_code=404, detail="应用不存在")
    
    # 读取并返回 HTML 文件内容
    async with aiofiles.open(app_file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    
    return HTMLResponse(content=content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 