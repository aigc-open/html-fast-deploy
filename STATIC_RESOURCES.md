# 静态资源支持说明

## 概述

HTML Fast Deploy 支持完整的静态资源部署，通过 **Referer 头隔离机制** 确保不同应用的静态资源完全隔离，避免资源混用。

## 核心特性

### 🔒 应用隔离机制
- **基于 Referer 头**: 系统通过 HTTP Referer 头判断静态资源请求来源
- **严格隔离**: 不同应用的静态资源完全隔离，无法跨应用访问
- **安全防护**: 防止恶意访问和资源泄露

### 📄 HTML 保持原样
- **不修改 HTML**: 系统不会修改 HTML 文件中的静态资源路径
- **相对路径支持**: 支持相对路径引用静态资源
- **外部链接支持**: 支持外部 CDN 链接，不会被错误替换

## 支持的部署方式

### 1. 单个 HTML 文件
- 适用于简单的单页面应用
- 直接上传 `.html` 文件
- 所有样式和脚本都内嵌在 HTML 中

### 2. ZIP 压缩包（推荐）
- 适用于包含静态资源的完整应用
- 上传包含所有文件的 ZIP 压缩包
- 自动解压和部署

## ZIP 压缩包结构

```
your-app.zip
├── index.html          # 主页面（必需）
├── style.css           # 样式文件
├── script.js           # JavaScript 文件
├── logo.png            # 图片资源
├── images/             # 图片目录
│   ├── image1.jpg
│   └── image2.jpg
└── assets/             # 其他资源目录
    ├── fonts/
    └── icons/
```

## 静态资源访问机制

### 在 HTML 中引用静态资源

```html
<!-- CSS 文件 - 相对路径 -->
<link rel="stylesheet" href="style.css">

<!-- JavaScript 文件 - 相对路径 -->
<script src="script.js"></script>

<!-- 图片文件 - 相对路径 -->
<img src="logo.png" alt="Logo">
<img src="images/banner.jpg" alt="Banner">

<!-- 外部链接 - 不会被修改 -->
<img src="https://cdn.example.com/image.jpg" alt="External Image">
<link rel="stylesheet" href="https://cdn.example.com/style.css">

<!-- 字体文件 -->
<link rel="stylesheet" href="assets/fonts/custom-font.css">
```

### 访问路径示例

假设应用名为 `my-app`：

**应用主页面**：
- `http://your-domain/apps/my-app`

**静态资源访问**：
- `http://your-domain/apps/my-app/style.css`
- `http://your-domain/apps/my-app/script.js`
- `http://your-domain/apps/my-app/logo.png`
- `http://your-domain/apps/my-app/images/banner.jpg`

### 隔离机制工作原理

1. **浏览器请求**: 浏览器从 `http://your-domain/apps/my-app` 加载 HTML
2. **HTML 解析**: HTML 中的相对路径被浏览器解析
3. **资源请求**: 浏览器请求 `http://your-domain/apps/my-app/style.css`
4. **Referer 检查**: 服务器检查 Referer 头为 `http://your-domain/apps/my-app`
5. **应用识别**: 从 Referer 中提取应用名称 `my-app`
6. **资源服务**: 从 `apps/my-app/style.css` 提供文件

## 支持的文件类型

### 图片文件
- `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.ico`

### 样式文件
- `.css`

### 脚本文件
- `.js`

### 字体文件
- `.woff`, `.woff2`, `.ttf`, `.eot`

### 其他文件
- `.json`, `.xml`, `.txt` 等

## 安全特性

### ✅ 允许的访问
- 正确 Referer 头访问对应应用的静态资源
- 外部 CDN 链接（不会被系统处理）

### ❌ 拒绝的访问
- 无 Referer 头的静态资源请求
- 错误 Referer 头访问其他应用的资源
- 恶意跨应用资源访问

### 错误处理示例

```bash
# ✅ 正确访问
curl -H "Referer: http://localhost:8000/apps/my-app" \
     http://localhost:8000/apps/my-app/style.css
# 返回: 200 OK

# ❌ 错误 Referer
curl -H "Referer: http://localhost:8000/apps/other-app" \
     http://localhost:8000/apps/my-app/style.css
# 返回: 404 Not Found

# ❌ 无 Referer
curl http://localhost:8000/apps/my-app/style.css
# 返回: 404 Not Found
```

## 使用示例

### 1. 创建应用目录结构
```
my-app/
├── index.html
├── style.css
├── script.js
├── logo.png
└── images/
    ├── hero.jpg
    └── icon.svg
```

### 2. 压缩为 ZIP 文件
将整个 `my-app` 目录压缩为 `my-app.zip`

### 3. 上传部署
在管理界面中：
1. 点击"创建新应用"
2. 输入应用名称（如：`my-app`）
3. 选择 ZIP 文件上传
4. 点击"创建应用"

### 4. 访问应用
应用部署后可通过以下地址访问：
- 主页面：`http://your-domain/apps/my-app`
- 静态资源自动通过 Referer 机制隔离访问

## 最佳实践

### 1. 文件组织
- 使用清晰的目录结构组织静态资源
- 将图片放在 `images/` 目录
- 将字体放在 `fonts/` 目录
- 将第三方库放在 `lib/` 目录

### 2. 路径引用
- 使用相对路径引用静态资源
- 避免使用绝对路径
- 外部资源使用完整的 URL

### 3. 文件优化
- 压缩 CSS 和 JavaScript 文件
- 优化图片文件大小
- 使用适当的文件格式

## 注意事项

1. **必需文件**: ZIP 压缩包中必须包含 `index.html` 文件
2. **路径引用**: 在 HTML 中使用相对路径引用静态资源
3. **文件大小**: 建议单个 ZIP 文件不超过 50MB
4. **文件编码**: 确保 HTML 文件使用 UTF-8 编码
5. **Referer 依赖**: 静态资源访问依赖 Referer 头，某些特殊情况下可能无法访问

## 故障排除

### 问题：静态资源无法加载
**可能原因**：
1. Referer 头缺失或错误
2. 文件路径不正确
3. 文件不存在于应用目录中

**解决方案**：
1. 检查浏览器开发者工具的网络请求
2. 确认 Referer 头正确设置
3. 验证文件存在于应用目录中

### 问题：跨应用资源访问被拒绝
**原因**: 这是正常的安全机制，防止资源混用

**解决方案**：
1. 确保从正确的应用页面访问资源
2. 检查 Referer 头是否正确
3. 不要尝试直接访问其他应用的资源

### 问题：外部图片无法显示
**可能原因**：
1. 外部链接失效
2. 网络连接问题
3. CORS 策略限制

**解决方案**：
1. 检查外部链接是否有效
2. 考虑将外部资源下载到本地
3. 使用可靠的 CDN 服务

### 问题：CSS 样式未生效
**解决方案**：
1. 检查 CSS 文件路径
2. 确认 CSS 语法正确
3. 验证文件编码为 UTF-8
4. 检查浏览器缓存

## 技术实现

### 核心逻辑
```python
# 从 Referer 头提取应用名称
referer = request.headers.get("referer", "")
match = re.search(r'/apps/([^/]+)', referer)
app_name = match.group(1) if match else None

# 在对应应用目录中查找静态资源
if app_name and is_valid_app_name(app_name):
    app_dir = APPS_DIR / app_name
    static_path = app_dir / file_path
    if static_path.exists():
        return serve_static_file(static_path, file_path)
```

### 日志记录
系统使用 loguru 记录详细的访问日志：
- **INFO**: 正常访问和资源查找
- **WARNING**: Referer 头缺失或解析失败
- **ERROR**: 资源不存在或访问被拒绝

## 更新日志

### v2.0.0 (当前版本)
- ✅ 实现基于 Referer 头的静态资源隔离
- ✅ 移除 HTML 路径自动替换功能
- ✅ 支持外部链接不被错误修改
- ✅ 添加专业的日志记录系统
- ✅ 增强安全性和错误处理 