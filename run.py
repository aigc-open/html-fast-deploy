#!/usr/bin/env python3
"""
HTML Fast Deploy 启动脚本
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """主启动函数"""
    print("🚀 HTML Fast Deploy 启动中...")
    
    # 检查必要的目录
    apps_dir = Path("apps")
    templates_dir = Path("templates")
    static_dir = Path("static")
    
    # 创建必要的目录
    apps_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    print(f"✅ 应用目录: {apps_dir.absolute()}")
    print(f"✅ 模板目录: {templates_dir.absolute()}")
    print(f"✅ 静态文件目录: {static_dir.absolute()}")
    
    # 检查环境变量文件
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  未找到 .env 文件，将使用默认配置")
        print("💡 建议创建 .env 文件并配置用户账号")
        print("📝 参考 env.example 文件")
    else:
        print("✅ 找到 .env 配置文件")
    
    # 检查是否有应用
    html_files = list(apps_dir.glob("*.html"))
    if html_files:
        print(f"📱 发现 {len(html_files)} 个应用:")
        for file in html_files:
            print(f"   - {file.stem}")
    else:
        print("📱 暂无应用，请登录后创建应用")
    
    print("\n🌐 启动 Web 服务器...")
    print("📍 访问地址: http://localhost:8000")
    print("🔑 默认账号: admin / admin123")
    print("⏹️  按 Ctrl+C 停止服务\n")
    
    try:
        # 启动服务器
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            # reload=True,
            log_level="info",
            workers=10
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 