"""
春节旅游计划AI小助手
使用Gradio构建Web界面，通过ModelArts Studio API实现AI功能
国家和地区列表通过大模型动态获取
"""

import os
import gradio as gr
import requests
import json
import re

# 从环境变量获取API配置
API_URL = os.environ.get("API_URL", "")
MODEL_NAME = os.environ.get("MODEL_NAME", "")
API_KEY = os.environ.get("API_KEY", "")

# 交通方式
TRANSPORT_MODES = ["自驾", "公共交通（飞机/火车/高铁/长途汽车）"]

# 缓存国家和城市数据
countries_cache = None
cities_cache = {}


def call_ai_api(prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
    """调用ModelArts Studio API"""
    if not API_URL or not API_KEY or not MODEL_NAME:
        return "错误：API配置不完整，请检查环境变量设置。"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "错误：API请求超时，请稍后重试。"
    except requests.exceptions.RequestException as e:
        return f"错误：API请求失败 - {str(e)}"
    except (KeyError, IndexError) as e:
        return f"错误：API响应格式异常 - {str(e)}"


def fetch_countries_from_ai():
    """通过AI获取世界上所有热门旅游国家列表"""
    global countries_cache
    
    if countries_cache is not None:
        return countries_cache

    prompt = """请列出世界上所有热门旅游国家，要求：
1. 按照热门程度排序，列出至少30个国家
2. 只输出国家名称，用中文逗号分隔
3. 不要输出任何其他内容，不要编号，不要解释

输出格式示例：中国,日本,韩国,泰国,美国,法国..."""

    system_prompt = "你是一位专业的旅游顾问，熟悉世界各地的旅游信息。请严格按照要求输出，只输出国家名称列表。"

    result = call_ai_api(prompt, system_prompt, max_tokens=1000)
    
    # 解析结果
    if result.startswith("错误"):
        # 如果API调用失败，返回默认列表
        countries_cache = ["中国", "日本", "韩国", "泰国", "新加坡", "马来西亚", "越南", 
                          "印度尼西亚", "法国", "意大利", "英国", "美国", "澳大利亚", 
                          "阿联酋", "瑞士", "德国", "西班牙", "希腊", "土耳其", "埃及"]
    else:
        # 清理并解析结果
        result = result.strip()
        # 移除可能的编号和多余字符
        result = re.sub(r'[\d\.\、\n]+', '', result)
        countries = [c.strip() for c in result.split(',') if c.strip()]
        countries_cache = countries if countries else ["中国", "日本", "韩国"]
    
    return countries_cache


def fetch_cities_from_ai(country: str):
    """通过AI获取指定国家的热门旅游城市列表"""
    global cities_cache
    
    if country in cities_cache:
        return cities_cache[country]

    prompt = f"""请列出{country}所有热门旅游城市，要求：
1. 按照热门程度排序，列出至少5-15个城市或地区
2. 只输出城市名称，用中文逗号分隔
3. 不要输出任何其他内容，不要编号，不要解释

输出格式示例：北京,上海,广州,深圳,成都..."""

    system_prompt = "你是一位专业的旅游顾问，熟悉世界各地的旅游信息。请严格按照要求输出，只输出城市名称列表。"

    result = call_ai_api(prompt, system_prompt, max_tokens=500)
    
    # 解析结果
    if result.startswith("错误"):
        # 如果API调用失败，返回空列表
        cities_cache[country] = []
    else:
        # 清理并解析结果
        result = result.strip()
        # 移除可能的编号和多余字符
        result = re.sub(r'[\d\.\、\n]+', '', result)
        cities = [c.strip() for c in result.split(',') if c.strip()]
        cities_cache[country] = cities if cities else []
    
    return cities_cache[country]


def load_countries_on_start():
    """应用启动时加载国家列表"""
    countries = fetch_countries_from_ai()
    return gr.Dropdown(choices=countries, value=None)


def update_regions(country, loading_status):
    """根据选择的国家更新地区下拉框"""
    if not country:
        return gr.Dropdown(choices=[], value=None, interactive=True), loading_status
    
    # 更新加载状态
    status_html = f'<span class="loading-status">正在获取 {country} 的热门城市...</span>'
    
    # 获取城市列表
    cities = fetch_cities_from_ai(country)
    
    if cities:
        status_html = f'<span class="loading-status">已加载 {country} 的 {len(cities)} 个热门城市（也可手动输入）</span>'
        return gr.Dropdown(choices=cities, value=None, interactive=True), status_html
    else:
        status_html = f'<span class="loading-status">请手动输入 {country} 的城市名称</span>'
        return gr.Dropdown(choices=[], value=None, interactive=True), status_html


def recommend_attractions(country, region):
    """AI推荐景点和天气信息"""
    if not country or not region:
        return "请先选择或输入国家和地区。"

    prompt = f"""请为春节旅游推荐{country}{region}的知名景点。
要求：
1. 列出3-5个最值得游览的景点，每个景点简要说明特色
2. 预测{region}未来7天的大致天气情况（温度范围、是否可能下雨等）
3. 给出春节期间游览的注意事项和建议

请用清晰的格式输出，使用中文。"""

    system_prompt = "你是一位专业的旅游顾问，熟悉世界各地的旅游景点和气候特点。请提供详细、实用的旅游建议。"

    return call_ai_api(prompt, system_prompt)


def get_attraction_info(attraction_name):
    """获取景点介绍和天气信息"""
    if not attraction_name or attraction_name.strip() == "":
        return "请输入景点名称。"

    prompt = f"""请介绍景点：{attraction_name}
要求：
1. 详细介绍该景点的历史背景、主要特色、游览亮点
2. 推荐最佳游览时间和游览路线
3. 预测该景点所在地未来7天的大致天气情况
4. 春节期间游览的特别提示

请用清晰的格式输出，使用中文。"""

    system_prompt = "你是一位专业的旅游顾问，熟悉世界各地的旅游景点。请提供详细、准确的景点介绍和实用建议。"

    return call_ai_api(prompt, system_prompt)


def plan_route(start_point, end_point, transport_mode):
    """规划出行路线"""
    if not start_point or not end_point or not transport_mode:
        return "请填写完整的出发地、目的地和交通方式。"

    if start_point.strip() == end_point.strip():
        return "出发地和目的地不能相同。"

    prompt = f"""请规划从{start_point}到{end_point}的{transport_mode}出行路线。

要求：
1. 如果是自驾：
   - 推荐最佳行驶路线
   - 预估行驶时间和距离
   - 途经的主要城市或服务区
   - 油费/过路费预估
   - 自驾注意事项

2. 如果是公共交通：
   - 推荐最佳的交通组合方式（飞机/火车/高铁/长途汽车）
   - 各段行程的时间和费用预估
   - 换乘站点和注意事项
   - 购票建议

3. 春节期间出行的特别提示

请用清晰的格式输出，使用中文。"""

    system_prompt = "你是一位专业的出行规划师，熟悉各种交通方式和路线规划。请提供详细、实用的出行建议。"

    return call_ai_api(prompt, system_prompt)


# 创建Gradio界面
with gr.Blocks(
    title="春节旅游计划AI小助手",
    theme=gr.themes.Soft(
        primary_hue="red",
        secondary_hue="orange",
        neutral_hue="slate",
    ),
    css="""
    .gradio-container {
        background: linear-gradient(135deg, #fff5f5 0%, #fff8e1 100%);
    }
    .title-container {
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #c62828, #d84315);
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(198, 40, 40, 0.3);
    }
    .title-container h1 {
        color: white;
        margin: 0;
        font-size: 2.2em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .title-container p {
        color: #ffecb3;
        margin: 10px 0 0 0;
        font-size: 1.1em;
    }
    .section-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid #ffcdd2;
    }
    .btn-primary {
        background: linear-gradient(90deg, #c62828, #d84315) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
    }
    .btn-primary:hover {
        background: linear-gradient(90deg, #b71c1c, #bf360c) !important;
    }
    .loading-status {
        color: #666;
        font-size: 0.9em;
        padding: 5px 10px;
        background: #fff3e0;
        border-radius: 5px;
        margin-top: 5px;
    }
    .output-markdown {
        background: #fafafa;
        border-radius: 10px;
        padding: 15px;
        min-height: 300px;
        border: 1px solid #e0e0e0;
    }
    .output-markdown h1, .output-markdown h2, .output-markdown h3 {
        color: #c62828;
        margin-top: 15px;
    }
    .output-markdown ul, .output-markdown ol {
        padding-left: 20px;
    }
    .output-markdown li {
        margin: 8px 0;
    }
    .output-markdown strong {
        color: #d84315;
    }
    """
) as demo:

    # 标题
    gr.HTML("""
    <div class="title-container">
        <h1>🎊 春节旅游计划AI小助手 🎊</h1>
        <p>智能规划您的春节假期，让旅途更加精彩！</p>
    </div>
    """)

    # 功能1：目的地推荐
    with gr.Tab("🌍 目的地推荐"):
        with gr.Column():
            gr.HTML('<div class="section-card">')
            gr.Markdown("### 选择您的旅游目的地")
            gr.Markdown("选择国家和城市，AI将为您推荐当地知名景点和天气信息\n\n💡 国家和城市列表由AI动态生成，首次加载可能需要几秒钟\n\n✏️ **您也可以直接输入小众国家或城市名称**")

            with gr.Row():
                country_dropdown = gr.Dropdown(
                    choices=[],
                    label="选择或输入国家（支持手动输入）",
                    interactive=True,
                    scale=1,
                    allow_custom_value=True
                )
                refresh_countries_btn = gr.Button("🔄 刷新列表", size="sm", scale=0)

            with gr.Row():
                region_dropdown = gr.Dropdown(
                    choices=[],
                    label="选择或输入地区/城市（支持手动输入）",
                    interactive=True,
                    scale=1,
                    allow_custom_value=True
                )
                refresh_cities_btn = gr.Button("🔄 刷新城市", size="sm", scale=0)

            loading_status = gr.HTML(
                value='<span class="loading-status">正在加载国家列表...</span>',
                visible=True
            )

            recommend_btn = gr.Button("🎯 获取推荐", variant="primary", elem_classes=["btn-primary"])
            gr.HTML('</div>')

            gr.HTML('<div class="section-card">')
            recommend_output = gr.Markdown(
                label="AI推荐结果",
                elem_classes=["output-markdown"]
            )
            gr.HTML('</div>')

            # 刷新国家列表按钮事件
            def refresh_countries():
                global countries_cache
                countries_cache = None
                countries = fetch_countries_from_ai()
                return gr.Dropdown(choices=countries, value=None), f'<span class="loading-status">已加载 {len(countries)} 个热门国家</span>'

            refresh_countries_btn.click(
                fn=refresh_countries,
                outputs=[country_dropdown, loading_status]
            )

            # 刷新城市列表按钮事件
            def refresh_cities(country):
                if not country:
                    return gr.Dropdown(choices=[], value=None), '<span class="loading-status">请先选择或输入国家</span>'
                global cities_cache
                if country in cities_cache:
                    del cities_cache[country]
                cities = fetch_cities_from_ai(country)
                if cities:
                    return gr.Dropdown(choices=cities, value=None), f'<span class="loading-status">已加载 {country} 的 {len(cities)} 个热门城市</span>'
                return gr.Dropdown(choices=[], value=None), f'<span class="loading-status">获取 {country} 的城市失败，请手动输入</span>'

            refresh_cities_btn.click(
                fn=refresh_cities,
                inputs=[country_dropdown],
                outputs=[region_dropdown, loading_status]
            )

            # 国家选择联动地区
            country_dropdown.change(
                fn=update_regions,
                inputs=[country_dropdown, loading_status],
                outputs=[region_dropdown, loading_status]
            )

            # 推荐按钮事件
            recommend_btn.click(
                fn=recommend_attractions,
                inputs=[country_dropdown, region_dropdown],
                outputs=[recommend_output]
            )

    # 功能2：景点查询
    with gr.Tab("🏛️ 景点查询"):
        with gr.Column():
            gr.HTML('<div class="section-card">')
            gr.Markdown("### 查询景点信息")
            gr.Markdown("输入景点名称，AI将为您详细介绍并提供天气信息")

            attraction_input = gr.Textbox(
                label="输入景点名称",
                placeholder="例如：故宫、埃菲尔铁塔、富士山...",
                lines=1
            )

            query_btn = gr.Button("🔍 查询景点", variant="primary", elem_classes=["btn-primary"])
            gr.HTML('</div>')

            gr.HTML('<div class="section-card">')
            attraction_output = gr.Markdown(
                label="景点介绍",
                elem_classes=["output-markdown"]
            )
            gr.HTML('</div>')

            query_btn.click(
                fn=get_attraction_info,
                inputs=[attraction_input],
                outputs=[attraction_output]
            )

    # 功能3：路线规划
    with gr.Tab("🚗 路线规划"):
        with gr.Column():
            gr.HTML('<div class="section-card">')
            gr.Markdown("### 规划出行路线")
            gr.Markdown("输入出发地、目的地和交通方式，AI将为您规划最佳路线")

            with gr.Row():
                start_input = gr.Textbox(
                    label="出发地",
                    placeholder="例如：北京、上海虹桥机场...",
                    scale=1
                )
                end_input = gr.Textbox(
                    label="目的地",
                    placeholder="例如：三亚、杭州西湖...",
                    scale=1
                )

            transport_dropdown = gr.Dropdown(
                choices=TRANSPORT_MODES,
                label="交通方式",
                interactive=True
            )

            plan_btn = gr.Button("🗺️ 规划路线", variant="primary", elem_classes=["btn-primary"])
            gr.HTML('</div>')

            gr.HTML('<div class="section-card">')
            route_output = gr.Markdown(
                label="路线规划结果",
                elem_classes=["output-markdown"]
            )
            gr.HTML('</div>')

            plan_btn.click(
                fn=plan_route,
                inputs=[start_input, end_input, transport_dropdown],
                outputs=[route_output]
            )

    # 底部信息
    gr.HTML("""
    <div style="text-align: center; padding: 20px; color: #666;">
        <p>💡 提示：AI生成的内容仅供参考，实际出行请以官方信息为准</p>
        <p>Powered by ModelArts Studio API</p>
    </div>
    """)

    # 应用加载时初始化国家列表
    demo.load(
        fn=load_countries_on_start,
        outputs=[country_dropdown]
    )


if __name__ == "__main__":
    # 检查环境变量
    if not API_URL or not MODEL_NAME or not API_KEY:
        print("警告：API环境变量未完整设置，请检查以下环境变量：")
        print("  - API_URL")
        print("  - MODEL_NAME")
        print("  - API_KEY")

    # 启动应用
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
