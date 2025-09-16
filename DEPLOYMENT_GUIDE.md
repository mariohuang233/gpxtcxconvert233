# GPX转TCX应用 - 部署指南

本指南将帮助您将GPX转TCX转换器部署到各种云平台。

## 🚀 快速部署选项

### 1. Render部署（推荐）

**优势：** 免费额度充足，配置简单，自动HTTPS

#### 步骤：
1. 将代码推送到GitHub仓库
2. 访问 [Render.com](https://render.com)
3. 点击 "New +" → "Web Service"
4. 连接GitHub仓库并选择此项目
5. Render会自动检测 `render.yaml` 配置
6. 点击 "Create Web Service" 开始部署

#### 配置信息：
- **运行时：** Python 3.11
- **构建命令：** `pip install -r requirements.txt`
- **启动命令：** `python3 web_app.py`
- **端口：** 8080
- **健康检查：** `/health`

### 2. Railway部署

**优势：** 部署速度快，开发者友好

#### 步骤：
1. 访问 [Railway.app](https://railway.app)
2. 连接GitHub仓库
3. 选择此项目进行部署
4. Railway会自动使用 `railway.toml` 配置

#### 或使用CLI：
```bash
npm install -g @railway/cli
railway login
railway deploy
```

### 3. Heroku部署

**优势：** 成熟稳定，文档完善

#### 步骤：
1. 安装Heroku CLI
2. 登录Heroku：`heroku login`
3. 创建应用：`heroku create your-app-name`
4. 部署：`git push heroku main`

#### 配置环境变量：
```bash
heroku config:set FLASK_ENV=production
heroku config:set PORT=8080
```

### 4. Docker部署

**优势：** 环境一致性，可部署到任何支持Docker的平台

#### 本地测试：
```bash
# 构建镜像
docker build -t gpx-to-tcx .

# 运行容器
docker run -p 8080:8080 gpx-to-tcx
```

#### 部署到云平台：
- **Google Cloud Run**
- **AWS ECS**
- **Azure Container Instances**

## 🔧 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `FLASK_ENV` | `development` | Flask环境（production/development） |
| `PORT` | `8888` | 应用端口 |
| `MAX_CONTENT_LENGTH` | `16777216` | 最大文件上传大小（16MB） |

## 📋 部署前检查清单

- [ ] 所有依赖已列在 `requirements.txt`
- [ ] 环境变量已正确配置
- [ ] 健康检查端点 `/health` 正常工作
- [ ] 静态文件路径正确
- [ ] 上传和输出目录权限正确

## 🛠️ 故障排除

### 常见问题：

1. **应用启动失败**
   - 检查Python版本（需要3.11+）
   - 确认所有依赖已安装
   - 查看启动日志

2. **文件上传失败**
   - 检查文件大小限制
   - 确认上传目录权限
   - 验证文件格式

3. **转换功能异常**
   - 检查GPX文件格式
   - 查看转换日志
   - 验证配置参数

### 日志查看：

**Render：**
```bash
# 在Render控制台查看实时日志
```

**Railway：**
```bash
railway logs
```

**Heroku：**
```bash
heroku logs --tail
```

## 🔒 安全配置

### 生产环境建议：

1. **设置安全的SECRET_KEY**
2. **启用HTTPS**（大多数平台自动提供）
3. **配置文件上传限制**
4. **设置适当的CORS策略**
5. **启用日志记录**

### 环境变量示例：
```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
MAX_CONTENT_LENGTH=16777216
```

## 📊 监控和维护

### 健康检查：
应用提供 `/health` 端点用于健康检查，返回：
- 应用状态
- 系统资源使用情况
- 依赖服务状态

### 性能监控：
- 内置埋点统计系统
- 访问 `/analytics` 查看使用统计
- 监控文件转换成功率

### 定期维护：
- 自动清理临时文件（24小时）
- 监控磁盘空间使用
- 更新依赖包

## 🆘 获取帮助

如果遇到部署问题：

1. 查看应用日志
2. 检查平台状态页面
3. 参考平台官方文档
4. 检查GitHub Issues

---

**部署成功后，您的GPX转TCX转换器将可以通过Web界面访问，支持文件上传、实时转换和配置自定义！**