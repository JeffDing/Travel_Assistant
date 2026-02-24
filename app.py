#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
春节旅游计划AI小助手
使用Gradio + OpenAI兼容API实现

支持的API类型：
- OpenAI官方API
- ModelArts Studio API
- 其他OpenAI兼容的API（如Azure、Anthropic、本地部署等）
"""

import os
import re
import time
import traceback
import gradio as gr
from openai import OpenAI
from datetime import datetime, timedelta
from functools import lru_cache

# 从环境变量获取API配置
API_URL = os.getenv("API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_KEY = os.getenv("API_KEY")

# 国家和地区数据
COUNTRIES_REGIONS = {
    "中国": {
        "北京": ["故宫", "天安门广场", "长城", "颐和园", "天坛", "南锣鼓巷", "什刹海"],
        "上海": ["外滩", "东方明珠", "南京路", "豫园", "迪士尼乐园", "田子坊"],
        "广州": ["广州塔", "白云山", "陈家祠", "沙面岛", "长隆旅游度假区"],
        "成都": ["大熊猫基地", "宽窄巷子", "锦里", "武侯祠", "都江堰", "青城山"],
        "西安": ["兵马俑", "大雁塔", "古城墙", "回民街", "华清池", "大唐芙蓉园"],
        "杭州": ["西湖", "灵隐寺", "雷峰塔", "宋城", "千岛湖", "西溪湿地"],
        "三亚": ["亚龙湾", "天涯海角", "南山寺", "蜈支洲岛", "亚特兰蒂斯"],
        "重庆": ["洪崖洞", "解放碑", "磁器口", "长江索道", "武隆天坑", "大足石刻"],
        "桂林": ["漓江", "象鼻山", "阳朔西街", "龙脊梯田", "遇龙河"],
        "厦门": ["鼓浪屿", "曾厝垵", "南普陀寺", "环岛路", "中山路"]
    },
    "日本": {
        "东京": ["东京塔", "浅草寺", "秋叶原", "银座", "新宿", "迪士尼乐园", "涩谷"],
        "大阪": ["大阪城", "道顿堀", "心斋桥", "环球影城", "奈良公园"],
        "京都": ["清水寺", "金阁寺", "伏见稻荷大社", "岚山", "二条城"],
        "北海道": ["小樽运河", "札幌雪祭", "函馆夜景", "富良野花田"]
    },
    "韩国": {
        "首尔": ["景福宫", "明洞", "弘大", "江南", "南山塔", "东大门"],
        "釜山": ["海云台", "甘川文化村", "札嘎其市场", "梵鱼寺"],
        "济州岛": ["汉拿山", "城山日出峰", "牛岛", "涉地可支"]
    },
    "泰国": {
        "曼谷": ["大皇宫", "玉佛寺", "考山路", "湄南河", "唐人街"],
        "清迈": ["素贴寺", "宁曼路", "清迈古城", "周末夜市"],
        "普吉岛": ["芭东海滩", "普吉镇", "卡伦海滩", "皮皮岛"]
    },
    "新加坡": {
        "新加坡市": ["滨海湾花园", "鱼尾狮", "圣淘沙", "乌节路", "牛车水", "克拉码头"]
    },
    "马来西亚": {
        "吉隆坡": ["双子塔", "独立广场", "茨厂街", "黑风洞", "云顶高原"],
        "槟城": ["乔治市街头艺术", "槟城山", "极乐寺", "巴都丁宜海滩"],
        "沙巴": ["京那巴鲁山", "海豚岛", "仙本那", "东姑阿都拉曼海洋公园"]
    },
    "越南": {
        "河内": ["还剑湖", "胡志明纪念堂", "三十六行街", "文庙"],
        "胡志明市": ["统一宫", "中央邮局", "圣母大教堂", "滨城市场"],
        "岘港": ["美溪海滩", "会安古镇", "巴拿山", "五行山"]
    },
    "美国": {
        "纽约": ["自由女神像", "时代广场", "中央公园", "帝国大厦", "大都会博物馆"],
        "洛杉矶": ["好莱坞", "迪士尼乐园", "环球影城", "圣莫尼卡海滩", "比佛利山庄"],
        "旧金山": ["金门大桥", "渔人码头", "九曲花街", "恶魔岛", "硅谷"]
    },
    "法国": {
        "巴黎": ["埃菲尔铁塔", "卢浮宫", "凯旋门", "香榭丽舍大街", "圣母院", "蒙马特高地"]
    },
    "英国": {
        "伦敦": ["大本钟", "伦敦眼", "白金汉宫", "大英博物馆", "塔桥", "海德公园"]
    },
    "澳大利亚": {
        "悉尼": ["悉尼歌剧院", "海港大桥", "邦迪海滩", "达令港", "蓝山"],
        "墨尔本": ["大洋路", "菲利普岛", "墨尔本CBD", "皇家植物园"]
    }
}

# 旅行风格选项
TRAVEL_STYLES = [
    "人文历史",
    "自然风光",
    "美食探索",
    "亲子休闲",
    "浪漫蜜月",
    "户外探险",
    "城市购物",
    "宗教文化",
    "摄影采风",
    "深度体验",
    "休闲度假",
    "其他"
]

# 地区列表缓存（优化性能）
REGION_CACHE = {country: list(regions.keys()) for country, regions in COUNTRIES_REGIONS.items()}

# 星期映射表（英文转中文）
WEEKDAY_MAP = {"Mon": "周一", "Tue": "周二", "Wed": "周三", "Thu": "周四", "Fri": "周五", "Sat": "周六", "Sun": "周日"}

class TravelAssistant:
    """春节旅游计划AI助手类"""

    def __init__(self):
        self.api_url = API_URL
        self.model_name = MODEL_NAME
        self.api_key = API_KEY

        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )

        # 验证配置
        if not self.api_key:
            print("⚠️  警告：API_KEY未设置")

    def post_process_response(self, response_text: str) -> str:
        """
        对AI返回的响应进行后处理，根据上下文统一替换雨具相关词汇

        Args:
            response_text: AI返回的原始文本

        Returns:
            处理后的文本
        """
        # 1. 自驾出行 + 台风/恶劣天气场景：替换为"带上雨衣雨披"
        # 匹配自驾相关的台风、恶劣天气提示
        driving_typhoon_pattern = r'(自驾|驾驶|车距|减速|行驶).*?(台风|暴雨|暴雪|恶劣天气|大暴雨|特大暴雨|强降雨).*?建议您(.*?)雨(具|伞|衣|披)'
        response_text = re.sub(driving_typhoon_pattern, r'\1\2，建议您带上雨衣雨披', response_text)

        # 2. 台风、恶劣天气(暴雨、暴雪等)场景：替换为"穿雨衣雨披"
        # 匹配台风、暴雨、暴雪等恶劣天气的提示
        typhoon_pattern = r'(台风|暴雨|暴雪|恶劣天气|大暴雨|特大暴雨|强降雨).*?建议您(.*?)雨(具|伞|衣|披)'
        response_text = re.sub(typhoon_pattern, r'\1，建议您穿雨衣雨披', response_text)

        # 3. 自驾出行 + 普通雨天场景：替换为"带上雨具"
        # 匹配自驾相关的普通雨天提示
        driving_rain_pattern = r'(自驾|驾驶|车距|减速|行驶).*?(降雨|下雨|小雨|中雨|大雨|雨天).*?建议您(.*?)雨(具|伞|衣|披)'
        response_text = re.sub(driving_rain_pattern, r'\1\2，建议您带上雨具', response_text)

        # 4. 其他雨天场景：替换为"带上雨具"
        # 匹配普通雨天
        rain_pattern = r'(降雨|下雨|小雨|中雨|大雨|雨天).*?建议您(.*?)雨(具|伞|衣|披)'
        response_text = re.sub(rain_pattern, r'\1，建议您带上雨具', response_text)

        # 去除重复表述
        pattern = r'(建议.*?雨(具|衣披).*?)，.*?最好.*?雨(具|衣披)'
        response_text = re.sub(pattern, r'\1', response_text)

        # 去除连续重复的"雨衣雨披"或"雨具"
        while '雨衣雨披和雨衣雨披' in response_text or '雨衣雨披、雨衣雨披' in response_text or '雨衣雨披，雨衣雨披' in response_text or '雨衣雨披,雨衣雨披' in response_text or '雨衣雨披与雨衣雨披' in response_text:
            response_text = response_text.replace('雨衣雨披和雨衣雨披', '雨衣雨披')
            response_text = response_text.replace('雨衣雨披、雨衣雨披', '雨衣雨披')
            response_text = response_text.replace('雨衣雨披，雨衣雨披', '雨衣雨披')
            response_text = response_text.replace('雨衣雨披,雨衣雨披', '雨衣雨披')
            response_text = response_text.replace('雨衣雨披与雨衣雨披', '雨衣雨披')
        
        # 去除"雨衣雨披雨披"等重复模式
        while '雨衣雨披雨披' in response_text:
            response_text = response_text.replace('雨衣雨披雨披', '雨衣雨披')
        while '雨披雨披' in response_text:
            response_text = response_text.replace('雨披雨披', '雨披')
        while '雨衣雨衣' in response_text:
            response_text = response_text.replace('雨衣雨衣', '雨衣')

        while '雨具和雨具' in response_text or '雨具、雨具' in response_text or '雨具，雨具' in response_text or '雨具,雨具' in response_text or '雨具与雨具' in response_text:
            response_text = response_text.replace('雨具和雨具', '雨具')
            response_text = response_text.replace('雨具、雨具', '雨具')
            response_text = response_text.replace('雨具，雨具', '雨具')
            response_text = response_text.replace('雨具,雨具', '雨具')
            response_text = response_text.replace('雨具与雨具', '雨具')
        
        # 去除"雨具雨具"等重复模式
        while '雨具雨具' in response_text:
            response_text = response_text.replace('雨具雨具', '雨具')

        return response_text

    def call_ai_api(self, prompt: str, system_prompt: str = None, max_retries: int = 3, max_tokens: int = 8000) -> str:
        """
        使用OpenAI库调用AI API

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            max_retries: 最大重试次数（默认3次）
            max_tokens: 最大生成token数（默认8000）

        Returns:
            AI返回的响应文本
        """
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for attempt in range(max_retries):
            try:
                # 使用OpenAI库调用API
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=max_tokens
                )

                # 获取响应内容
                content = response.choices[0].message.content
                return self.post_process_response(content)

            except Exception as e:
                last_error = e
                error_msg = str(e)
                print(f"API调用错误 (尝试 {attempt + 1}/{max_retries}): {error_msg}")

                # 检查是否是可重试的错误
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue

        return f"调用AI服务时发生错误: 已重试{max_retries}次仍失败。错误信息: {str(last_error)}"

    def get_weather_info(self, location: str, days: int = 7) -> str:
        """
        获取天气信息（模拟数据，实际可接入真实天气API）

        Args:
            location: 地点名称
            days: 查询天数

        Returns:
            天气信息文本
        """
        # 计算具体日期
        today = datetime.now()
        date_list = []
        for i in range(1, days + 1):
            future_date = today + timedelta(days=i)
            # 格式：2月20日（周四）
            date_str = future_date.strftime("%m月%d日（%a）")
            # 将英文星期转换为中文
            for en, cn in WEEKDAY_MAP.items():
                date_str = date_str.replace(en, cn)
            date_list.append(date_str)
        
        date_range = "、".join(date_list)

        prompt = f"""请为{location}生成未来{days}天的天气预报信息。
注意：这是春节旅游期间，请根据该地点的气候特点给出合理的天气预测。
请以表格形式展示，包含日期、天气状况、温度范围（最高温/最低温）、风力风向、穿衣建议等。

【重要】日期显示要求：
- 请使用具体日期显示，不要使用"第1天"、"第2天"等表述
- 日期范围：{date_range}
- 表格中的日期列请直接显示具体日期（如"2月20日"）

【重要提醒】
如果预报中包含以下天气情况，请在天气预报后添加醒目的出行建议：
- 雨天（小雨、中雨、大雨等）：请添加"☔ 温馨提示：预计有降雨，建议您带上雨具，注意出行安全。"
- 台风天气：请添加"🌀 温馨提示：预计有台风影响，建议您穿雨衣雨披，注意出行安全。"
- 暴雨、暴雪等恶劣天气：请添加"⚠️ 温馨提示：预计有恶劣天气，建议您穿雨衣雨披，注意出行安全。"
- 雪天：请添加"❄️ 温馨提示：预计有降雪，建议您携带防寒装备，注意保暖和防滑。"
- 大风天气：请添加"💨 温馨提示：预计有大风，建议您注意防风，避免户外高空活动。"

请用醒目的格式（如加粗、emoji等）突出显示这些安全提醒。"""

        system_prompt = """你是一个专业的天气预报助手，请根据地点的气候特点和季节特点，生成合理详细的天气预报信息，并在恶劣天气时提供安全出行建议。"""

        return self.call_ai_api(prompt, system_prompt)

    def get_attraction_info(self, attraction: str) -> tuple[str, str]:
        """
        获取景点介绍信息和天气

        Args:
            attraction: 景点名称

        Returns:
            (景点介绍, 天气信息)
        """

        prompt = f"""请详细介绍景点"{attraction}"，包括以下内容：
1. 景点位置和基本信息
2. 历史文化背景
3. 主要特色和看点
4. 最佳游览时间
5. 游玩建议和注意事项
6. 推荐游玩时长
7. 门票信息（如有）
8. 周边配套设施

请用清晰的结构化方式呈现，便于阅读。"""

        system_prompt = """你是一个专业的旅游景点介绍专家，请提供准确、详细、实用的景点介绍信息。"""

        attraction_info = self.call_ai_api(prompt, system_prompt)
        weather_info = self.get_weather_info(attraction, days=7)

        return attraction_info, weather_info

    def recommend_attractions(self, country: str, city: str = None) -> tuple[str, str]:
        """
        推荐目的地知名景点和天气

        Args:
            country: 国家
            city: 城市/地区

        Returns:
            (景点推荐, 天气信息)
        """
        location = f"{country}{city}" if city else country

        prompt = f"""请推荐{location}春节期间值得游览的知名景点，包括以下内容：
1. 推荐至少5-10个必游景点
2. 每个景点的简要介绍
3. 景点之间的游览顺序建议
4. 春节期间的特殊活动或氛围
5. 适合的游览天数建议
6. 交通方式建议

请用清晰的结构化方式呈现，便于游客参考。"""

        system_prompt = """你是一个专业的旅游规划师，熟悉全球各地的旅游景点，能够为游客提供实用的景点推荐建议。"""

        attractions = self.call_ai_api(prompt, system_prompt)
        weather = self.get_weather_info(location, days=7)

        return attractions, weather

    def plan_route(self, start: str, end: str, transport_type: str) -> str:
        """
        规划出行交通路线

        Args:
            start: 起点
            end: 终点
            transport_type: 交通方式（自驾/公共交通）

        Returns:
            路线规划信息
        """
        if transport_type == "自驾":
                prompt = f"""请为从{start}到{end}的自驾路线提供详细的规划建议，包括：

    【基础路线信息】
    1. 推荐的行驶路线和高速公路
    2. 预计行驶距离和耗时
    3. 路况注意事项和驾驶建议
    4. 可能的替代路线
    5. 春节期间高速免费政策和限行提醒（如适用）
    6. 停车建议

    【服务区休息建议】（重要）
    7. 根据行驶距离和时长，推荐合理的休息时间间隔：
       - 建议每2-3小时或200公里休息一次
       - 长途驾驶建议每4小时进行一次较长时间休息（15-30分钟）
       - 标注最佳休息时间点和位置

    8. 推荐休息服务区列表：
       - 列出沿途主要服务区的名称、位置（距离起点的公里数）
       - 说明每个推荐服务区的设施情况（餐饮、加油、卫生间、便利店、WiFi、充电桩等）
       - 标注哪些服务区适合长时间休息（有餐厅、休息区），哪些适合短暂停留
       - 标注服务区的开放时间和春节营业情况

    【特色服务区推荐】（重点推荐）
    9. 美食特色服务区：
       - 推荐有地方特色美食的服务区（如阳澄湖服务区的大闸蟹、嘉兴服务区的粽子等）
       - 推荐有知名连锁餐厅的服务区
       - 推荐有特色小吃的服务区

    10. 景观特色服务区：
        - 推荐有特色景观或打卡点的服务区（如园林式服务区、观景台等）
        - 推荐建筑风格独特的服务区
        - 推荐周边有景点的服务区

    11. 服务优质服务区：
        - 推荐设施完善、服务优质的服务区（五星级服务区）
        - 推荐有特色商品或纪念品的服务区
        - 推荐有亲子设施、宠物友好等服务区

    12. 春节特色服务区：
        - 春节期间有特殊活动或装饰的服务区
        - 提供春节特色餐饮的服务区
        - 有年货市集的服务区

    【出行建议】
    13. 春节出行高峰期服务区拥挤预警和应对建议
    14. 服务区加油排队建议（建议避开高峰时段）
    15. 电动汽车充电服务区推荐（如有）

    【沿途天气预警】（重点提醒）
    16. 沿途天气情况：
       - 列出从{start}到{end}沿途主要城市/地区的天气情况
       - 包含天气状况、温度、风力风向等信息
       - 标注可能出现恶劣天气的路段

    17. 恶劣天气出行提醒（重要）：
       - 雨天提醒：☔ 温馨提示：沿途预计有降雨，建议您带上雨具，注意保持安全车距，减速慢行，谨慎驾驶。
       - 台风提醒：🌀 温馨提示：沿途预计有台风影响，建议您带上雨衣雨披，注意保持安全车距，减速慢行，谨慎驾驶。
       - 暴雨、暴雪等恶劣天气提醒：⚠️ 温馨提示：沿途预计有恶劣天气，建议您带上雨衣雨披，注意保持安全车距，减速慢行，谨慎驾驶。
       - 大风提醒：💨 温馨提示：沿途预计有大风天气，建议您注意防风，大型车辆需特别注意侧风影响，谨慎驾驶。
       - 雾霾提醒：🌫️ 温馨提示：沿途预计有雾霾天气，建议您开启雾灯，保持安全车距，必要时选择服务区休息等待天气好转。

    请用清晰的分段和列表形式呈现，便于驾驶员参考。特别注意春节出行高峰期，服务区可能较为拥挤，建议提前规划休息点。"""

                system_prompt = """你是一个专业的自驾路线规划师，熟悉全国高速公路服务区分布和特色，能够为用户提供详细、实用的自驾出行建议，特别是服务区休息规划和特色服务区推荐，以及沿途天气预警和恶劣天气出行提醒。"""
        else:  # 公共交通
            prompt = f"""请为从{start}到{end}的公共交通出行提供详细的规划建议，包括所有可能的交通方式：
1. 飞机：推荐航班、机场信息、飞行时长、价格区间
2. 火车/高铁：推荐车次、车站信息、运行时长、票价区间
3. 长途汽车：推荐班次、车站信息、运行时长、票价区间
4. 其他可能的交通方式（轮渡等）
5. 各种交通方式的优缺点对比
6. 推荐的最佳出行方案
7. 春节期间的购票提醒和注意事项
8. 城市内交通接驳建议

【沿途天气预警】（重点提醒）
9. 沿途天气情况：
   - 列出从{start}到{end}沿途主要城市/地区的天气情况
   - 包含天气状况、温度、风力风向等信息
   - 标注可能出现恶劣天气的路段

10. 恶劣天气出行提醒（重要）：
    - 雨天提醒：☔ 温馨提示：沿途预计有降雨，建议您带上雨具，注意出行安全。
    - 台风提醒：🌀 温馨提示：沿途预计有台风影响，建议您穿雨衣雨披，注意出行安全。
    - 暴雨、暴雪等恶劣天气提醒：⚠️ 温馨提示：沿途预计有恶劣天气，建议您穿雨衣雨披，注意出行安全。
    - 大风提醒：💨 温馨提示：沿途预计有大风天气，建议您注意防风，避免户外高空活动。

请提供全面的公共交通出行方案。"""

            system_prompt = """你是一个专业的公共交通出行规划师，熟悉各种交通方式，能够为用户提供全面的出行方案，以及沿途天气预警和恶劣天气出行提醒。"""

        return self.call_ai_api(prompt, system_prompt)

    def plan_itinerary(self, destination: str, days: int, travel_style: str) -> str:
        """
        规划每日游玩行程

        Args:
            destination: 目的地
            days: 游玩天数
            travel_style: 游玩风格

        Returns:
            每日行程规划
        """
        # 计算具体日期
        today = datetime.now()
        date_list = []
        for i in range(1, days + 1):
            future_date = today + timedelta(days=i)
            # 格式：2月20日（周四）
            date_str = future_date.strftime("%m月%d日（%a）")
            # 将英文星期转换为中文
            for en, cn in WEEKDAY_MAP.items():
                date_str = date_str.replace(en, cn)
            date_list.append(date_str)
        
        date_range = "、".join(date_list)

        prompt = f"""请为{destination}制定一个{days}天的详细行程规划，游玩风格为：{travel_style}。

【重要】日期信息：
- 行程日期范围：{date_range}
- 请在每天的行程开头显示具体日期（如"## 📅 第1天 - 02月20日（周四）"）

要求：
1. 每天的行程安排要合理，不要过于紧凑或松散
2. 每天上午、下午、晚上的具体活动安排
3. 包含景点游览、美食推荐、购物等
4. 考虑景点之间的地理位置，优化路线
5. 提供交通方式建议
6. 包含用餐推荐
7. 每天的预算预估
8. 特别注意事项
9. 春节期间的特色活动或氛围
10. 根据"{travel_style}"风格重点突出相关内容

【天气与出行提示】（重要）
11. 请为每一天的行程添加天气情况预测：
    - 在每天行程开头显示当日天气（如"🌤️ 天气：晴，温度 15-22℃，微风"）
    - 根据该地点的气候特点和季节给出合理的天气预测
    
12. 根据天气情况给出出行提示（重要格式要求）：
    - 天气提示必须在天气信息下方**换行**单独显示
    - 格式示例：
      ```
      🌤️ 天气：晴，温度 15-22℃，微风
      
      ☔ 温馨提示：预计有降雨，建议您带上雨具，注意出行安全。
      ```
    - 雨天（小雨、中雨、大雨等）：添加"☔ 温馨提示：预计有降雨，建议您带上雨具，注意出行安全。"
    - 台风天气：添加"🌀 温馨提示：预计有台风影响，建议您穿雨衣雨披，注意出行安全。"
    - 暴雨、暴雪等恶劣天气：添加"⚠️ 温馨提示：预计有恶劣天气，建议您穿雨衣雨披，注意出行安全。"
    - 雪天：添加"❄️ 温馨提示：预计有降雪，建议您携带防寒装备，注意保暖和防滑。"
    - 大风天气：添加"💨 温馨提示：预计有大风，建议您注意防风，避免户外高空活动。"
    - 高温天气（35℃以上）：添加"🌡️ 温馨提示：预计高温天气，建议您做好防晒防暑，多补充水分。"
    - 低温天气（0℃以下）：添加"🥶 温馨提示：预计低温天气，建议您注意保暖，穿戴厚实衣物。"

请按天详细列出，便于执行。如果天数较长，可以安排返程或休息日。"""

        system_prompt = """你是一个专业的行程规划师，能够根据用户的需求和喜好，制定详细、实用、个性化的旅游行程计划。你需要根据目的地的气候特点和季节，为每天的行程提供合理的天气预测和相应的出行建议。"""

        return self.call_ai_api(prompt, system_prompt)

# 全局实例
assistant = TravelAssistant()

# 性能优化：使用LRU缓存减少重复计算
@lru_cache(maxsize=32)
def get_regions_cached(country: str) -> tuple:
    """缓存版本的地区获取函数"""
    if country and country in REGION_CACHE:
        regions = tuple(REGION_CACHE[country])  # 转为tuple以便缓存
        default_value = regions[0] if len(regions) > 0 else None
        return (regions, default_value)
    return (tuple(), None)
def update_regions(country: str):
    """根据选择的国家更新地区下拉框（Gradio 6.5.1优化版本 - 使用缓存）"""
    try:
        if not country or not isinstance(country, str):
            return gr.update(choices=[], value=None, allow_custom_value=True)

        matched_country = None
        for c in REGION_CACHE.keys():
            if c.lower() == country.lower():
                matched_country = c
                break

        if matched_country:
            regions, default_value = get_regions_cached(matched_country)
            return gr.update(choices=list(regions), value=default_value, allow_custom_value=True)

        # 自定义国家：调用AI获取推荐城市
        try:
            prompt = f"""请推荐{country}最适合旅游的5-8个城市或地区。
请直接列出城市名称，用逗号分隔，不要添加其他说明。
例如：东京,大阪,京都,北海道,福冈"""
            
            system_prompt = """你是一个专业的旅游顾问，熟悉全球各国的旅游城市。请简洁地列出城市名称。"""
            cities_text = assistant.call_ai_api(prompt, system_prompt)
            
            cities = []
            for city in cities_text.replace('，', ',').split(','):
                city = city.strip()
                if city and len(city) < 20 and not any(x in city for x in ['推荐', '城市', '地区', '旅游', '例如', '如下', '以下']):
                    cities.append(city)
            
            if cities:
                return gr.update(choices=cities, value=cities[0], allow_custom_value=True)
        except Exception as e:
            print(f"获取自定义国家城市失败: {e}")

        return gr.update(choices=[], value=None, allow_custom_value=True)
    except Exception as e:
        print(f"update_regions错误: {e}\n{traceback.format_exc()}")
        return gr.update(choices=[], value=None, allow_custom_value=True)

def recommend_attractions_handler(country: str, city: str):
    """处理景点推荐请求"""
    try:
        if not country:
            return "请先选择国家/地区", ""
        attractions, weather = assistant.recommend_attractions(country, city if city else None)
        return attractions, weather
    except Exception as e:
        error_msg = f"获取推荐时发生错误: {str(e)}"
        print(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg, ""

def get_attraction_info_handler(attraction: str):
    """处理景点查询请求"""
    try:
        if not attraction:
            return "请输入景点名称", ""
        info, weather = assistant.get_attraction_info(attraction)
        return info, weather
    except Exception as e:
        error_msg = f"查询景点时发生错误: {str(e)}"
        print(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg, ""

def plan_route_handler(start: str, end: str, transport_type: str) -> str:
    """处理路线规划请求"""
    try:
        if not start or not end:
            return "请输入起点和终点"
        return assistant.plan_route(start, end, transport_type)
    except Exception as e:
        error_msg = f"规划路线时发生错误: {str(e)}"
        print(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg

def plan_itinerary_handler(destination: str, days: int, travel_style: str) -> str:
    """处理行程规划请求"""
    try:
        if not destination or not days:
            return "请输入目的地和游玩天数"
        return assistant.plan_itinerary(destination, days, travel_style)
    except Exception as e:
        error_msg = f"规划行程时发生错误: {str(e)}"
        print(f"{error_msg}\n{traceback.format_exc()}")
        return error_msg

def create_interface():
    """创建Gradio界面"""
    custom_css = """
    .gradio-container {
        font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif !important;
    }

    .header {
        text-align: center;
        padding: 30px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .header h1 {
        color: white;
        font-size: 2.5em;
        margin: 0;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }

    .header p {
        color: rgba(255, 255, 255, 0.95);
        font-size: 1.1em;
        margin-top: 10px;
    }

    .tab-content {
        padding: 20px;
    }

    .info-box {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
    }

    .result-box {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-top: 15px;
        max-height: 800px;
        overflow-y: auto;
    }

    .result-box::-webkit-scrollbar {
        width: 8px;
    }

    .result-box::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }

    .result-box::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }

    .result-box::-webkit-scrollbar-thumb:hover {
        background: #555;
    }

    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 12px 30px !important;
        border-radius: 25px !important;
        transition: all 0.3s ease !important;
    }

    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    .input-box {
        border-radius: 10px !important;
    }

    .dropdown {
        border-radius: 10px !important;
    }

    .label {
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    /* 行程规划输出区域 - 支持超长文本 */
    .itinerary-output {
        max-height: 1200px !important;
        overflow-y: auto !important;
        padding: 20px !important;
        background: #ffffff !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 10px !important;
    }
    
    .itinerary-output::-webkit-scrollbar {
        width: 10px;
    }
    
    .itinerary-output::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 5px;
    }
    
    .itinerary-output::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 5px;
    }
    
    .itinerary-output::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    """

    with gr.Blocks(css=custom_css, title="春节旅游计划AI助手") as app:
        gr.HTML("""
        <div class="header">
            <h1>🧧 春节旅游计划AI助手 🧧</h1>
            <p>智能规划您的春节假期 · 探索精彩世界</p>
        </div>
        """)

        with gr.Tabs():
            with gr.TabItem("🌍 目的地推荐", id=1):
                gr.Markdown("### 选择您的旅行目的地，获取景点推荐和天气信息")

                with gr.Row():
                    with gr.Column(scale=1):
                        country_dropdown = gr.Dropdown(
                            choices=list(COUNTRIES_REGIONS.keys()),
                            label="选择国家/地区",
                            info="选择您想去的旅游国家或地区，也支持手动输入",
                            interactive=True,
                            allow_custom_value=True  # Gradio 6.5.1: 允许手动输入
                        )

                        city_dropdown = gr.Dropdown(
                            choices=list(COUNTRIES_REGIONS.get("中国", {}).keys()),
                            value=list(COUNTRIES_REGIONS.get("中国", {}).keys())[0] if COUNTRIES_REGIONS.get("中国") else None,
                            label="选择城市",
                            info="选择该国家或地区的下一级城市，也支持手动输入",
                            interactive=True,
                            allow_custom_value=True  # Gradio 6.5.1: 允许手动输入
                        )

                        recommend_btn = gr.Button("🔍 获取推荐", variant="primary", size="lg")

                    with gr.Column(scale=2):
                        attractions_output = gr.Markdown(
                            label="景点推荐",
                            value="请选择国家/地区和城市，然后点击获取推荐"
                        )

                        weather_output = gr.Markdown(
                            label="天气预报",
                            value="天气信息将在这里显示"
                        )

                country_dropdown.change(
                    fn=update_regions,
                    inputs=country_dropdown,
                    outputs=city_dropdown
                )

                recommend_btn.click(
                    fn=recommend_attractions_handler,
                    inputs=[country_dropdown, city_dropdown],
                    outputs=[attractions_output, weather_output]
                )

            with gr.TabItem("🏛️ 景点查询", id=2):
                gr.Markdown("### 输入景点名称，获取详细介绍和天气信息")

                with gr.Row():
                    with gr.Column(scale=1):
                        attraction_input = gr.Textbox(
                            label="景点名称",
                            placeholder="例如：故宫、埃菲尔铁塔、富士山...",
                            info="支持手动输入任意景点名称"
                        )

                        attraction_query_btn = gr.Button("🔍 查询景点", variant="primary", size="lg")

                    with gr.Column(scale=2):
                        attraction_info_output = gr.Markdown(
                            label="景点介绍",
                            value="景点介绍信息将在这里显示"
                        )

                        attraction_weather_output = gr.Markdown(
                            label="天气信息",
                            value="天气信息将在这里显示"
                        )

                attraction_query_btn.click(
                    fn=get_attraction_info_handler,
                    inputs=[attraction_input],
                    outputs=[attraction_info_output, attraction_weather_output]
                )

            with gr.TabItem("🚗 交通路线规划", id=3):
                gr.Markdown("### 规划您的出行路线")

                with gr.Row():
                    with gr.Column(scale=1):
                        start_point = gr.Textbox(
                            label="出发地",
                            placeholder="例如：北京、上海..."
                        )

                        end_point = gr.Textbox(
                            label="目的地",
                            placeholder="例如：三亚、成都..."
                        )

                        transport_type = gr.Radio(
                            choices=["自驾", "公共交通"],
                            value="自驾",
                            label="交通方式",
                            info="选择您的出行方式"
                        )

                        route_btn = gr.Button("🗺️ 规划路线", variant="primary", size="lg")

                    with gr.Column(scale=2):
                        route_output = gr.Markdown(
                            label="路线规划",
                            value="路线规划信息将在这里显示"
                        )

                route_btn.click(
                    fn=plan_route_handler,
                    inputs=[start_point, end_point, transport_type],
                    outputs=[route_output]
                )

            with gr.TabItem("📅 行程规划", id=4):
                gr.Markdown("### 制定您的详细游玩行程")

                with gr.Row():
                    with gr.Column(scale=1):
                        itinerary_destination = gr.Textbox(
                            label="目的地",
                            placeholder="例如：北京、巴黎、东京..."
                        )

                        itinerary_days = gr.Slider(
                            minimum=1,
                            maximum=15,
                            value=3,
                            step=1,
                            label="游玩天数",
                            info="选择您的游玩天数"
                        )

                        itinerary_style = gr.Dropdown(
                            choices=TRAVEL_STYLES,
                            value="人文历史",
                            label="游玩风格",
                            info="选择您偏好的游玩风格"
                        )

                        custom_style = gr.Textbox(
                            label="自定义风格（可选）",
                            placeholder="如果上述选项不合适，可以手动输入...",
                            info="手动输入您的游玩偏好"
                        )

                        itinerary_btn = gr.Button("📋 生成行程", variant="primary", size="lg")

                    with gr.Column(scale=2):
                        itinerary_output = gr.Markdown(
                            label="行程规划",
                            value="行程规划信息将在这里显示",
                            elem_classes=["result-box", "itinerary-output"],
                            latex_delimiters=[],
                            show_copy_button=True
                        )

                itinerary_btn.click(
                    fn=plan_itinerary_handler,
                    inputs=[itinerary_destination, itinerary_days, itinerary_style],
                    outputs=[itinerary_output]
                )

        # 页脚
        gr.HTML("""
        <div style="text-align: center; padding: 20px; color: #666; margin-top: 30px;">
            <p>💡 提示：所有功能均由AI驱动，建议结合实际情况进行调整</p>
            <p style="margin-top: 10px;">Powered by ModelArts Studio | 春节旅游计划AI助手</p>
        </div>
        """)

    return app

def main():
    """主函数"""
    print("=" * 60)
    print("春节旅游计划AI助手")
    print("=" * 60)
    print(f"API URL: {API_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"API Key: {'已设置' if API_KEY else '未设置'}")
    print("=" * 60)

    if not API_KEY:
        print("⚠️  警告：API_KEY未设置，请确保环境变量已配置")

    if not API_URL:
        print("⚠️  警告：API_URL未设置，请确保环境变量已配置")

    if not MODEL_NAME:
        print("⚠️  警告：MODEL_NAME未设置，请确保环境变量已配置")

    print("\n使用OpenAI库调用API，支持任何OpenAI兼容的服务：")
    print("  - OpenAI官方API")
    print("  - ModelArts Studio API")
    print("  - Azure OpenAI")
    print("  - 本地部署（Ollama、vLLM等）")
    print("  - 其他OpenAI兼容API")
    print("\n环境变量配置示例:")
    print("  # OpenAI官方")
    print("  export API_URL=https://api.openai.com/v1")
    print("  export MODEL_NAME=gpt-4")
    print("  export API_KEY=sk-your-api-key")
    print("")
    print("  # ModelArts或其他兼容服务")
    print("  export API_URL=https://your-endpoint/v1")
    print("  export MODEL_NAME=your-model-name")
    print("  export API_KEY=your-api-key")
    print("=" * 60)

    app = create_interface()

    app.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
