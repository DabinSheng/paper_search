#!/bin/bash

# 学术文献检索Agent启动脚本

echo "🚀 启动学术文献检索Agent..."
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8或更高版本"
    exit 1
fi

# 检查是否存在虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查并安装依赖
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "📥 安装依赖包..."
    pip install -r requirements.txt
    touch venv/.dependencies_installed
else
    echo "✅ 依赖包已安装"
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到.env文件"
    echo "📝 正在从.env.example创建.env文件..."
    cp .env.example .env
    echo ""
    echo "⚠️  请编辑 .env 文件，填入你的 QWEN_API_KEY"
    echo "   获取API Key: https://dashscope.console.aliyun.com/"
    echo ""
    read -p "按Enter键继续..."
fi

# 启动应用
echo ""
echo "🎉 启动Streamlit应用..."
echo "📱 应用将在浏览器中自动打开"
echo "🔗 如未自动打开，请访问: http://localhost:8501"
echo ""
echo "💡 提示: 按 Ctrl+C 停止应用"
echo ""

streamlit run app.py
