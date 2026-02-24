#!/bin/bash

# 春节旅游计划AI助手启动脚本
# ============================================
# 配置您的API信息（请修改下面的值）
# ============================================

# API基础地址
# OpenAI官方: https://api.openai.com/v1
# ModelArts Studio: https://your-endpoint/v1
# Azure OpenAI: https://your-resource.openai.azure.com
# 本地部署(Ollama): http://localhost:11434/v1
export API_BASE_URL="https://api.openai.com/v1"

# 模型名称
# OpenAI: gpt-4, gpt-3.5-turbo
# ModelArts: 根据您的模型名称
# 本地: 根据您部署的模型名称
export MODEL_NAME="gpt-3.5-turbo"

# API密钥（请替换为您的实际密钥）
export API_KEY="your-api-key-here"

# ============================================
# 以下为启动逻辑，无需修改
# ============================================

# 显示配置信息（隐藏敏感信息）
echo "=========================================="
echo "春节旅游计划AI助手"
echo "=========================================="
echo "API Base URL: $API_BASE_URL"
echo "Model: $MODEL_NAME"
echo "API Key: ${API_KEY:0:8}...${API_KEY: -4}"  # 只显示前8位和后4位
echo "=========================================="
echo ""

# 检查API_KEY是否已配置
if [ "$API_KEY" = "your-api-key-here" ]; then
    echo "警告: API_KEY 尚未配置！"
    echo "请编辑 run.sh 文件，设置您的 API_KEY"
    echo ""
    read -p "是否继续启动？(y/n): " continue_start
    if [ "$continue_start" != "y" ] && [ "$continue_start" != "Y" ]; then
        echo "已取消启动"
        exit 1
    fi
fi

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python 3.7+"
    exit 1
fi

# 检查pip是否可用
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "错误: 未找到pip，请先安装pip"
    exit 1
fi

# 使用pip3或pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# 检查并安装依赖
echo "检查并安装依赖..."
$PIP_CMD install --upgrade pip -q
$PIP_CMD install gradio openai -q

# 启动应用
echo ""
echo "启动应用..."
echo "应用将在 http://localhost:7860 上运行"
echo "按 Ctrl+C 可停止应用"
echo "=========================================="
echo ""

# 运行应用
python3 app.py
