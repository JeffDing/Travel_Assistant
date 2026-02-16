#!/bin/bash

# 春节旅游计划AI小助手启动脚本
# 设置API环境变量并启动应用

# 设置API配置环境变量
export API_URL="API_URL"
export MODEL_NAME="MODEL_NAME"
export API_KEY="API_KEY"

# 打印启动信息
echo "=========================================="
echo "  春节旅游计划AI小助手"
echo "=========================================="
echo ""
echo "API配置信息："
echo "  API_URL: $API_URL"
echo "  MODEL_NAME: $MODEL_NAME"
echo "  API_KEY: ${API_KEY:0:10}..." # 只显示前10个字符
echo ""
echo "正在启动应用..."
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 启动Python应用
python app.py
