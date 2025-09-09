#!/bin/bash

# GPX to TCX Converter - 快速启动脚本
# 作者: mariohuang

echo "🚀 启动 GPX to TCX Converter"
echo "============================="
echo "作者: mariohuang"
echo "声明: 本应用仅用于测试场景，不能作为比赛作弊用途"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo "✅ 依赖检查完成"
else
    echo "⚠️  requirements.txt 未找到"
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p uploads outputs
echo "✅ 目录创建完成"

# 启动应用
echo "🌐 启动Web应用..."
echo "访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止应用"
echo ""
python3 web_app.py