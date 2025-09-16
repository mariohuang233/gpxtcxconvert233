# 🥷 秘术 - GPX转TCX转换器

**作者：mariohuang**  
**声明：本应用仅用于测试场景，不能作为比赛作弊用途**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Railway-purple.svg)](https://railway.app)

## 🏃‍♂️ 项目简介

这是一个现代化的Web应用程序，专门用于将GPX格式的GPS轨迹文件转换为TCX格式。采用Apple风格的暗黑主题设计，提供专业级的运动数据转换服务，特别适用于跑步、骑行等运动数据的格式转换和优化。

### 🎯 核心价值
- **专业转换**: 高精度的GPX到TCX格式转换
- **数据增强**: 智能补充心率、步频、功率等运动数据
- **用户体验**: Apple风格界面设计，操作简洁直观
- **性能优化**: 高效的文件处理和转换算法

## ✨ 主要特性

- 🌐 **现代化Web界面** - 响应式设计，支持桌面和移动设备
- 📁 **拖拽上传** - 支持拖拽上传GPX文件，操作简便
- ⚙️ **灵活配置** - 可自定义运动类型、设备信息、心率、步频等参数
- 📊 **实时进度** - 转换过程实时显示，用户体验友好
- 🔄 **批量处理** - 支持多文件同时转换
- 📱 **移动优化** - 完美适配手机和平板设备
- 🚀 **云端部署** - 支持多种云平台部署

## 🛠️ 技术栈

- **后端**: Python 3.11 + Flask
- **前端**: HTML5 + CSS3 + JavaScript
- **数据处理**: lxml + 自定义GPX/TCX解析器
- **部署**: Railway / Render / Heroku
- **CI/CD**: GitHub Actions

## 🚀 快速开始

### 本地运行

1. **克隆仓库**
```bash
git clone https://github.com/你的用户名/gpx-to-tcx-converter.git
cd gpx-to-tcx-converter
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动应用**
```bash
python3 web_app.py
```

4. **访问应用**
打开浏览器访问 `http://localhost:8080`

### 云端部署

#### Railway 部署（推荐）

1. Fork 本仓库到你的GitHub账号
2. 访问 [Railway](https://railway.app) 并连接GitHub
3. 选择你的仓库进行部署
4. Railway会自动检测配置并部署应用

#### Render 部署

1. 访问 [Render](https://render.com)
2. 连接GitHub账号并选择仓库
3. 使用项目中的 `render.yaml` 配置自动部署

#### Heroku 部署

```bash
heroku create your-app-name
git push heroku main
```

详细部署说明请参考 [GitHub部署指南.md](./GitHub部署指南.md)

## 📖 使用说明

### 基本使用流程

1. **上传GPX文件**
   - 点击上传区域选择文件，或直接拖拽GPX文件到上传区域
   - 支持单个或多个文件同时上传

2. **配置转换参数**
   - **运动类型**: 跑步、骑行、其他
   - **设备信息**: 自定义设备名称和版本
   - **心率设置**: 静息心率、最大心率、心率区间
   - **步频配置**: 基础步频、最大步频
   - **功率设置**: 最小功率、最大功率
   - **时间格式**: 支持多种时间格式解析

3. **开始转换**
   - 点击"开始转换"按钮
   - 实时查看转换进度
   - 转换完成后自动下载TCX文件

### 高级功能

- **批量转换**: 同时处理多个GPX文件
- **进度监控**: 实时显示转换状态和进度
- **错误处理**: 详细的错误信息和处理建议
- **文件管理**: 自动清理临时文件

## 🔧 配置说明

### 环境变量

```bash
PORT=8080                    # 应用端口
FLASK_ENV=production         # 运行环境
MAX_CONTENT_LENGTH=16777216  # 最大文件大小(16MB)
```

### 文件结构

```
gpx-to-tcx-converter/
├── web_app.py              # 主应用文件
├── gpx_to_tcx.py          # 转换核心逻辑
├── requirements.txt        # Python依赖
├── static/
│   └── style.css          # 样式文件
├── templates/
│   └── index.html         # 前端模板
├── uploads/               # 上传文件目录
├── outputs/               # 输出文件目录
├── .github/
│   └── workflows/
│       └── deploy.yml     # GitHub Actions配置
├── railway.toml           # Railway部署配置
├── render.yaml            # Render部署配置
├── Procfile               # Heroku部署配置
└── runtime.txt            # Python版本配置
```

## 🧪 测试

### 本地测试

```bash
# 测试应用启动
python3 -c "from web_app import app; print('Flask app imported successfully')"

# 测试转换模块
python3 -c "import gpx_to_tcx; print('GPX to TCX module imported successfully')"
```

### 健康检查

应用提供健康检查端点：`/health`

```bash
curl http://localhost:8080/health
```

## 📊 监控和日志

### 系统监控

- CPU使用率监控
- 内存使用情况
- 磁盘空间检查
- 活跃任务统计

### 日志记录

- 转换过程日志
- 错误信息记录
- 性能指标统计

## 🔒 安全特性

- 文件类型验证（仅允许GPX文件）
- 文件大小限制（最大16MB）
- 自动文件清理
- 无敏感信息存储

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- 🌐 Web界面实现
- 📁 文件上传下载功能
- ⚙️ 参数配置功能
- 📊 实时进度显示
- 🚀 云端部署支持

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👤 作者信息

**mariohuang**
- GitHub: [@mariohuang](https://github.com/mariohuang)
- 项目链接: [https://github.com/mariohuang/gpx-to-tcx-converter](https://github.com/mariohuang/gpx-to-tcx-converter)

## ⚠️ 重要声明

**本应用仅用于测试和学习目的，不得用于任何形式的比赛作弊行为。**

使用本应用即表示您同意：
- 仅将此工具用于合法的数据格式转换
- 不将转换后的数据用于欺骗性竞赛提交
- 遵守相关运动组织的规则和条例

## 🆘 常见问题

### Q: 支持哪些GPX文件格式？
A: 支持标准GPX 1.1格式的文件，包含轨迹点、时间戳等基本信息。

### Q: 转换后的TCX文件兼容性如何？
A: 生成的TCX文件兼容Garmin Connect、Strava等主流运动平台。

### Q: 文件大小有限制吗？
A: 单个文件最大支持16MB，建议文件大小在10MB以内以获得最佳性能。

### Q: 数据安全如何保障？
A: 所有上传的文件在转换完成后会自动删除，不会在服务器上永久存储。

---

如果您觉得这个项目有用，请给它一个 ⭐ Star！