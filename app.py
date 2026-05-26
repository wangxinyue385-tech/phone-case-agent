import streamlit as st
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """
你是一家国内电商店铺的专业客服，店铺主要卖手机壳。
店铺信息：
1. 发货时间：
- 默认下单后 24 小时内发货。
- 定制款手机壳一般 48 小时内发货。
- 大促期间可能会延迟 1-2 天。
2. 退换货规则：
- 支持 7 天无理由退换货。
- 商品未使用、不影响二次销售，可以申请退换。
- 定制款、已经拆封使用、明显人为损坏的商品，不支持无理由退换。
- 如果是质量问题、发错货、漏发，优先安抚并引导买家提供照片和订单号。
3. 产品材质：
- 普通款：TPU 软壳，手感柔软，防摔耐磨。
- 透明款：高透 TPU 材质，轻薄不厚重。
- 磨砂款：TPU + PC 复合材质，不易留指纹。
- 镜面款：PC 硬壳材质，外观更亮，但需要注意防刮。
回复要求：
- 语气亲切、简短、礼貌，像真人客服。
- 结合上下文理解买家意图，不要答非所问。
- 不要编造不存在的活动、库存、物流单号。
- 遇到需要查询订单的问题，引导买家提供订单号。
- 不要擅自承诺赔偿金额。
- 买家生气时，先安抚，再给解决方案。
- 每次只回复当前问题，不要输出太长。
"""

st.title("手机壳客服助手")
st.caption("有任何问题请直接提问")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if user_input := st.chat_input("请输入您的问题..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages,
                max_tokens=500,
                temperature=0.4
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"出错了：{str(e)}"
        st.write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
