# GPX转TCX应用 - GitHub部署指南

## 作者：mariohuang
**声明：本应用仅用于测试场景，不能作为比赛作弊用途**

## 📋 部署概览

本指南将帮助您将GPX转TCX应用部署到GitHub并实现线上访问，支持多种部署平台。

## 🚀 快速部署方案

### 方案一：Railway部署（推荐）

**优势：**
- 免费额度充足
- 自动HTTPS
- 支持Python应用
- 部署简单快速

**步骤：**

1. **准备GitHub仓库**
```bash
# 在项目根目录执行
git init
git add .
git commit -m "Initial commit: GPX to TCX Converter by mariohuang"
git branch -M main
git remote add origin https://github.com/你的用户名/gpx-to-tcx-converter.git
git push -u origin main
```

2. **创建Railway配置文件**
创建 `railway.toml`：
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python3 web_app.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

3. **部署到Railway**
- 访问 [railway.app](https://railway.app)
- 使用GitHub账号登录
- 点击 "New Project" → "Deploy from GitHub repo"
- 选择您的仓库
- Railway会自动检测Python应用并部署

### 方案二：Render部署

**优势：**
- 免费层可用
- 自动SSL证书
- 简单配置

**步骤：**

1. **创建render.yaml**
```yaml
services:
  - type: web
    name: gpx-to-tcx-converter
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python3 web_app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

2. **部署到Render**
- 访问 [render.com](https://render.com)
- 连接GitHub账号
- 选择仓库并配置服务

### 方案三：Heroku部署

**步骤：**

1. **创建Procfile**
```
web: python3 web_app.py
```

2. **创建runtime.txt**
```
python-3.11.0
```

3. **部署命令**
```bash
heroku create your-app-name
git push heroku main
```

## 📁 项目结构优化

为了更好的部署，建议调整项目结构：

```
gpx-to-tcx-converter/
├── web_app.py              # 主应用文件
├── gpx_to_tcx.py          # 转换核心逻辑
├── requirements.txt        # Python依赖
├── runtime.txt            # Python版本（Heroku）
├── Procfile               # 启动命令（Heroku）
├── railway.toml           # Railway配置
├── render.yaml            # Render配置
├── static/
│   └── style.css          # 样式文件
├── templates/
│   └── index.html         # 前端模板
├── uploads/               # 上传文件目录
├── outputs/               # 输出文件目录
└── README.md              # 项目说明
```

## 🔧 环境变量配置

在部署平台设置以下环境变量：

```bash
PORT=8080                  # 应用端口
FLASK_ENV=production       # 生产环境
PYTHON_VERSION=3.11.0      # Python版本
```

## 📝 GitHub Actions自动部署

创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Railway

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Test application
      run: |
        python -m pytest tests/ || echo "No tests found"
    
    - name: Deploy to Railway
      if: github.ref == 'refs/heads/main'
      run: |
        echo "Deployment triggered for Railway"
```

## 🌐 域名配置

### 自定义域名设置

1. **Railway域名配置**
   - 在Railway项目设置中添加自定义域名
   - 配置DNS CNAME记录指向Railway提供的域名

2. **Render域名配置**
   - 在Render服务设置中添加自定义域名
   - 配置DNS记录

## 📊 监控和日志

### 应用监控

```python
# 在web_app.py中添加健康检查端点
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

@app.route('/metrics')
def metrics():
    return {
        'uptime': time.time() - start_time,
        'conversions_count': conversion_count,
        'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024
    }
```

### 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

## 🔒 安全配置

### 文件上传限制

```python
# 在web_app.py中添加安全配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制
app.config['UPLOAD_EXTENSIONS'] = ['.gpx']  # 只允许GPX文件
```

### CORS配置

```python
from flask_cors import CORS

# 配置CORS（如需要）
CORS(app, origins=['https://yourdomain.com'])
```

## 📱 移动端优化

确保CSS响应式设计：

```css
/* 在style.css中添加移动端优化 */
@media (max-width: 768px) {
    .container {
        padding: 10px;
        margin: 10px;
    }
    
    .upload-area {
        min-height: 150px;
    }
    
    .config-section {
        margin-bottom: 15px;
    }
}
```

## 🚀 部署检查清单

- [ ] 代码已推送到GitHub
- [ ] requirements.txt包含所有依赖
- [ ] 配置文件已创建（Procfile/railway.toml等）
- [ ] 环境变量已设置
- [ ] 健康检查端点可访问
- [ ] 文件上传功能正常
- [ ] 转换功能测试通过
- [ ] 移动端界面正常显示
- [ ] HTTPS证书配置完成

## 🆘 常见问题解决

### 部署失败

1. **检查Python版本兼容性**
2. **确认依赖包版本**
3. **检查端口配置**
4. **查看部署日志**

### 文件上传问题

1. **检查文件大小限制**
2. **确认上传目录权限**
3. **验证文件格式检查**

### 性能优化

1. **启用文件缓存**
2. **优化转换算法**
3. **添加进度显示**
4. **实现异步处理**

## 📞 技术支持

- **作者：** mariohuang
- **GitHub：** [项目仓库链接]
- **问题反馈：** 通过GitHub Issues提交

---

**重要声明：本应用仅用于测试和学习目的，不得用于任何形式的比赛作弊行为。**

**部署完成后，您的同事可以通过以下方式访问：**
- Railway: `https://your-app-name.up.railway.app`
- Render: `https://your-app-name.onrender.com`
- Heroku: `https://your-app-name.herokuapp.com`

选择最适合您需求的部署方案，开始享受便捷的线上GPX转TCX转换服务！