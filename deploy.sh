#!/bin/bash

# GPX to TCX Converter - 快速部署脚本
# 作者: mariohuang
# 声明: 本应用仅用于测试场景，不能作为比赛作弊用途

set -e

echo "🚀 GPX to TCX Converter - 快速部署脚本"
echo "==========================================="
echo "作者: mariohuang"
echo "声明: 本应用仅用于测试场景，不能作为比赛作弊用途"
echo ""

# 检查Git是否已安装
if ! command -v git &> /dev/null; then
    echo "❌ 错误: Git未安装，请先安装Git"
    exit 1
fi

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3未安装，请先安装Python3"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 获取GitHub仓库信息
read -p "请输入您的GitHub用户名: " GITHUB_USERNAME
read -p "请输入仓库名称 (默认: gpx-to-tcx-converter): " REPO_NAME
REPO_NAME=${REPO_NAME:-gpx-to-tcx-converter}

echo ""
echo "📋 配置信息:"
echo "   GitHub用户名: $GITHUB_USERNAME"
echo "   仓库名称: $REPO_NAME"
echo "   仓库URL: https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo ""

read -p "确认以上信息正确吗? (y/N): " CONFIRM
if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
    echo "❌ 部署已取消"
    exit 1
fi

echo ""
echo "🔧 开始部署流程..."
echo ""

# 1. 初始化Git仓库
echo "📁 初始化Git仓库..."
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git仓库初始化完成"
else
    echo "✅ Git仓库已存在"
fi

# 2. 添加文件到Git
echo "📝 添加文件到Git..."
git add .
echo "✅ 文件添加完成"

# 3. 提交更改
echo "💾 提交更改..."
if git diff --staged --quiet; then
    echo "ℹ️  没有新的更改需要提交"
else
    git commit -m "Initial commit: GPX to TCX Converter by mariohuang
    
    Features:
    - Web-based GPX to TCX conversion
    - Modern responsive UI
    - Real-time progress tracking
    - Batch file processing
    - Cloud deployment ready
    
    Author: mariohuang
    Note: This application is for testing purposes only"
    echo "✅ 更改提交完成"
fi

# 4. 设置主分支
echo "🌿 设置主分支..."
git branch -M main
echo "✅ 主分支设置完成"

# 5. 添加远程仓库
echo "🔗 添加远程仓库..."
REMOTE_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
if git remote get-url origin &> /dev/null; then
    git remote set-url origin $REMOTE_URL
    echo "✅ 远程仓库URL已更新"
else
    git remote add origin $REMOTE_URL
    echo "✅ 远程仓库已添加"
fi

# 6. 推送到GitHub
echo "⬆️  推送到GitHub..."
echo "注意: 如果这是第一次推送，您可能需要:"
echo "1. 在GitHub上创建仓库: https://github.com/new"
echo "2. 设置Git凭据或SSH密钥"
echo ""
read -p "准备好推送了吗? (y/N): " PUSH_CONFIRM
if [[ $PUSH_CONFIRM =~ ^[Yy]$ ]]; then
    if git push -u origin main; then
        echo "✅ 代码推送成功!"
    else
        echo "❌ 推送失败，请检查:"
        echo "   1. GitHub仓库是否已创建"
        echo "   2. Git凭据是否正确"
        echo "   3. 网络连接是否正常"
        echo ""
        echo "手动推送命令:"
        echo "   git push -u origin main"
        exit 1
    fi
else
    echo "ℹ️  跳过推送步骤"
    echo "手动推送命令:"
    echo "   git push -u origin main"
fi

echo ""
echo "🎉 部署准备完成!"
echo "=================="
echo ""
echo "📋 下一步操作:"
echo ""
echo "1. 🌐 访问您的GitHub仓库:"
echo "   https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "2. 🚀 选择部署平台:"
echo ""
echo "   Railway (推荐):"
echo "   • 访问: https://railway.app"
echo "   • 连接GitHub账号"
echo "   • 选择您的仓库进行部署"
echo "   • 自动检测railway.toml配置"
echo ""
echo "   Render:"
echo "   • 访问: https://render.com"
echo "   • 连接GitHub账号"
echo "   • 使用render.yaml配置部署"
echo ""
echo "   Heroku:"
echo "   • 安装Heroku CLI"
echo "   • 运行: heroku create $REPO_NAME"
echo "   • 运行: git push heroku main"
echo ""
echo "3. 📖 查看详细部署指南:"
echo "   cat GitHub部署指南.md"
echo ""
echo "4. 🧪 本地测试:"
echo "   python3 web_app.py"
echo "   访问: http://localhost:8080"
echo ""
echo "5. 🐳 Docker部署 (可选):"
echo "   docker-compose up -d"
echo ""
echo "⚠️  重要提醒:"
echo "   本应用仅用于测试场景，不能作为比赛作弊用途"
echo ""
echo "🎯 部署完成后，您的同事可以通过以下方式访问:"
echo "   • Railway: https://your-app-name.up.railway.app"
echo "   • Render: https://your-app-name.onrender.com"
echo "   • Heroku: https://your-app-name.herokuapp.com"
echo ""
echo "📞 技术支持:"
echo "   • GitHub Issues: https://github.com/$GITHUB_USERNAME/$REPO_NAME/issues"
echo "   • 作者: mariohuang"
echo ""
echo "感谢使用 GPX to TCX Converter! 🙏"