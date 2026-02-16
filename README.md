# 春节旅游计划AI助手

一个基于Python + Gradio + ModelArts Studio API的智能旅游规划小助手，帮助用户制定春节假期旅游计划。

## 功能特性

### 1. 🌍 目的地推荐
- 通过下拉框选择国家和城市
- 国家与城市联动选择
- AI推荐该地区的知名景点
- 提供未来7天天气预报

### 2. 🏛️ 景点查询
- 支持手动输入任意景点名称
- AI提供详细的景点介绍
- 包含历史文化背景、特色看点、游玩建议等
- 提供景点所在地的天气预报

### 3. 🚗 交通路线规划
- 支持自驾和公共交通两种方式
- 自驾：推荐路线、距离、耗时、休息点、停车建议
- 公共交通：飞机、火车、高铁、长途汽车等多种方案对比

### 4. 📅 行程规划
- 输入目的地和游玩天数
- 选择游玩风格（人文、自然、美食、亲子等12种风格）
- AI自动生成每日详细行程
- 包含景点、美食、交通、预算建议

## 环境变量配置

应用使用以下环境变量，后期修改API无需改动代码：

- `API_URL`: ModelArts Studio API地址
- `MODEL_NAME`: 使用的模型名称
- `API_KEY`: API访问密钥

环境变量已在 `run.sh` 脚本中设置，如需修改请编辑 `run.sh` 文件。

## 安装和运行

### 方法一：使用启动脚本（推荐）

```bash
cd travel
bash run.sh
```

启动脚本会自动：
1. 设置环境变量
2. 检查Python环境
3. 安装所需依赖
4. 启动应用

### 方法二：手动安装

```bash
cd travel

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export API_URL="https://api.modelarts-maas.com/v2/chat/completions"
export MODEL_NAME="deepseek-v3.2"
export API_KEY="your_api_key_here"

# 启动应用
python app.py
```

## 访问应用

应用启动后，在浏览器中访问：

```
http://localhost:7860
```

## 项目结构

```
travel/
├── app.py              # 主应用文件
├── run.sh              # 启动脚本（包含环境变量）
├── requirements.txt    # Python依赖
└── README.md          # 项目说明文档
```

## 技术栈

- **Python 3.7+**
- **Gradio 4.0+**: Web界面框架
- **Requests**: HTTP请求库
- **ModelArts Studio API**: AI服务

## 特色功能

1. **美观的界面设计**: 使用渐变色、圆角、阴影等现代设计元素
2. **智能联动**: 选择国家后自动更新城市列表
3. **灵活输入**: 既支持下拉选择，也支持手动输入（小众景点）
4. **全面规划**: 涵盖景点、天气、交通、行程等旅游全流程
5. **安全配置**: API密钥通过环境变量管理，不暴露在代码中

## 注意事项

- 确保网络连接正常，能够访问ModelArts Studio API
- API调用可能产生费用，请注意控制使用量
- 天气信息为AI生成，建议结合实际天气APP参考
- 路线和行程规划为AI建议，请根据实际情况调整

## 许可证

MIT License
