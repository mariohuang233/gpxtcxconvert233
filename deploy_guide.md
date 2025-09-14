# 🚀 GPX转TCX应用 - 一键部署指南

## 快速部署到线上平台

### 方法一：Railway部署（推荐）

1. **准备GitHub仓库**
   ```bash
   # 初始化Git仓库（如果还没有）
   git init
   git add .
   git commit -m "Initial commit"
   
   # 添加远程仓库
   git remote add origin https://github.com/你的用户名/gpx-to-tcx-converter.git
   git branch -M main
   git push -u origin main
   ```

2. **部署到Railway**
   - 访问 [railway.app](https://railway.app)
   - 使用GitHub账号登录
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择你的仓库
   - Railway会自动检测配置并部署
   - 几分钟后获得公开访问链接！

### 方法二：Render部署

1. **推送代码到GitHub**（同上）

2. **部署到Render**
   - 访问 [render.com](https://render.com)
   - 连接GitHub账号
   - 选择 "Web Service"
   - 选择你的仓库
   - 配置会自动从 `render.yaml` 读取
   - 点击部署

### 方法三：Heroku部署

1. **安装Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # 或访问 https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **部署到Heroku**
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   ```

## 🎯 部署后验证

部署成功后，访问你的应用链接：
- Railway: `https://你的应用名.railway.app`
- Render: `https://你的应用名.onrender.com`
- Heroku: `https://你的应用名.herokuapp.com`

### 功能测试清单
- ✅ 主页加载正常
- ✅ 天气信息显示
- ✅ 文件上传功能
- ✅ GPX转TCX转换
- ✅ 文件下载功能
- ✅ 移动端适配

## 🔧 环境变量配置

如需自定义配置，可在部署平台设置以下环境变量：

```
PORT=8080
FLASK_ENV=production
MAX_CONTENT_LENGTH=16777216
PYTHON_VERSION=3.11.0
```

## 📱 分享给同事

部署完成后，将链接分享给同事：

**"嘿！我部署了一个GPX转TCX转换器，你可以通过这个链接使用：**
**https://你的应用名.railway.app"**

## 🆘 常见问题

### 部署失败
1. 检查Python版本兼容性
2. 确认依赖包版本
3. 检查端口配置
4. 查看部署日志

### 功能异常
1. 检查文件大小限制
2. 确认上传目录权限
3. 验证API服务状态

---

**作者**: mariohuang  
**声明**: 本应用仅用于测试场景，不能作为比赛作弊用途