#!/bin/bash

# 春节旅游计划AI助手启动脚本
# 设置环境变量并启动应用

# 设置API配置环境变量
export API_URL="API_URL"
export MODEL_NAME="MODEL_NAME"
export API_KEY="API_KEY"

# 显示配置信息
echo "=========================================="
echo "春节旅游计划AI助手"
echo "=========================================="
echo "API URL: $API_URL"
echo "Model: $MODEL_NAME"
echo "API Key: ${API_KEY:0:10}..."  # 只显示前10个字符
echo "=========================================="
echo ""

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
$PIP_CMD install --upgrade pip
$PIP_CMD install gradio requests

# 启动应用
echo ""
echo "启动应用..."
echo "应用将在 http://localhost:7860 上运行"
echo "按 Ctrl+C 可停止应用"
echo "=========================================="
echo ""

# 运行应用
python3 app.py
