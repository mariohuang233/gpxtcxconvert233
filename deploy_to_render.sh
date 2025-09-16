#!/bin/bash

# GPX转TCX应用 - Render部署脚本
# 使用方法: ./deploy_to_render.sh

set -e

echo "🚀 开始部署GPX转TCX应用到Render..."

# 检查必要文件
echo "📋 检查部署文件..."
required_files=("web_app.py" "requirements.txt" "Dockerfile" "render.yaml")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done
echo "✅ 所有必要文件检查完成"

# 检查Git仓库状态
echo "📦 检查Git仓库状态..."
if [ ! -d ".git" ]; then
    echo "🔧 初始化Git仓库..."
    git init
    git add .
    git commit -m "Initial commit for GPX to TCX converter"
else
    echo "✅ Git仓库已存在"
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 发现未提交的更改，正在提交..."
    git add .
    git commit -m "Update for deployment $(date '+%Y-%m-%d %H:%M:%S')"
fi

echo "📋 部署前检查清单:"
echo "   ✅ 所有必要文件已准备"
echo "   ✅ Git仓库状态正常"
echo "   ✅ 代码已提交"

echo ""
echo "🌐 接下来的部署步骤:"
echo "1. 登录到 https://render.com"
echo "2. 点击 'New +' -> 'Web Service'"
echo "3. 连接你的GitHub仓库"
echo "4. 选择这个项目仓库"
echo "5. Render会自动检测到render.yaml配置文件"
echo "6. 点击 'Create Web Service' 开始部署"
echo ""
echo "📝 部署配置信息:"
echo "   - 运行时: Python 3.11"
echo "   - 端口: 8080"
echo "   - 健康检查: /health"
echo "   - 环境: Production"
echo ""
echo "🔗 部署完成后，你的应用将可以通过以下地址访问:"
echo "   https://your-app-name.onrender.com"
echo ""
echo "⚠️  注意事项:"
echo "   - 免费计划有使用限制"
echo "   - 应用在无活动时会休眠"
echo "   - 首次访问可能需要等待启动"
echo ""
echo "✅ 部署准备完成！请按照上述步骤在Render平台完成部署。"