#!/bin/bash

# API配置（请修改）
export API_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-3.5-turbo"
export API_KEY="your-api-key-here"

# 安装依赖并启动
pip install gradio openai -q 2>/dev/null || pip3 install gradio openai -q
python3 app.py
