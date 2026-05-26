from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

SYSTEM_PROMPT = (
    "你是一家国内电商店铺的专业客服，店铺主要卖手机壳。\n"
    "店铺信息：\n"
    "1. 发货时间：\n"
    "- 默认下单后 24 小时内发货。\n"
    "- 定制款手机壳一般 48 小时内发货。\n"
    "- 大促期间可能会延迟 1-2 天。\n"
    "2. 退换货规则：\n"
    "- 支持 7 天无理由退换货。\n"
    "- 商品未使用、不影响二次销售，可以申请退换。\n"
    "- 定制款、已经拆封使用、明显人为损坏的商品，不支持无理由退换。\n"
    "- 如果是质量问题、发错货、漏发，优先安抚并引导买家提供照片和订单号。\n"
    "3. 产品材质：\n"
    "- 普通款：TPU 软壳，手感柔软，防摔耐磨。\n"
    "- 透明款：高透 TPU 材质，轻薄不厚重。\n"
    "- 磨砂款：TPU + PC 复合材质，不易留指纹。\n"
    "- 镜面款：PC 硬壳材质，外观更亮，但需要注意防刮。\n"
    "回复要求：\n"
    "- 语气亲切、简短、礼貌，像真人客服。\n"
    "- 结合上下文理解买家意图，不要答非所问。\n"
    "- 不要编造不存在的活动、库存、物流单号。\n"
    "- 遇到需要查询订单的问题，引导买家提供订单号。\n"
    "- 不要擅自承诺赔偿金额。\n"
    "- 买家生气时，先安抚，再给解决方案。\n"
    "- 每次只回复当前问题，不要输出太长。"
)

HTML = '''
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>手机壳专卖店客服</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; }
.container { width: 100%; max-width: 480px; height: 100vh; background: white; display: flex; flex-direction: column; }
.header { background: linear-gradient(135deg, #FF6B35, #ff8c5a); color: white; padding: 20px; text-align: center; }
.header h1 { font-size: 20px; margin-bottom: 4px; }
.header p { font-size: 13px; opacity: 0.85; }
.messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.welcome { text-align: center; color: #aaa; font-size: 14px; margin-top: 20px; }
.msg { display: flex; gap: 8px; align-items: flex-end; }
.msg.user { flex-direction: row-reverse; }
.bubble { max-width: 75%; padding: 10px 14px; border-radius: 18px; font-size: 14px; line-height: 1.5; }
.msg.user .bubble { background: #FF6B35; color: white; border-bottom-right-radius: 4px; }
.msg.bot .bubble { background: #f0f0f0; color: #333; border-bottom-left-radius: 4px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.msg.user .avatar { background: #FF6B35; }
.msg.bot .avatar { background: #e0e0e0; }
.typing { display: none; }
.typing .bubble { background: #f0f0f0; color: #999; font-size: 13px; }
.bottom { border-top: 1px solid #eee; padding: 10px 12px; background: white; }
.quick-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.quick-btn { background: #fff3ee; border: 1px solid #FF6B35; color: #FF6B35; border-radius: 16px; padding: 5px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }
.quick-btn:hover { background: #FF6B35; color: white; }
.input-row { display: flex; gap: 8px; }
.input-row input { flex: 1; border: 1px solid #ddd; border-radius: 24px; padding: 10px 16px; font-size: 14px; outline: none; }
.input-row input:focus { border-color: #FF6B35; }
.input-row button { background: #FF6B35; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 18px; cursor: pointer; flex-shrink: 0; }
.input-row button:hover { background: #e55a25; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🛍️ 手机壳专卖店</h1>
    <p>专业客服在线，有问题尽管问～</p>
  </div>
  <div class="messages" id="messages">
    <div class="welcome">👋 你好！我是店铺客服，请问有什么可以帮您？</div>
  </div>
  <div class="bottom">
    <div class="quick-btns">
      <button class="quick-btn" onclick="sendMsg('什么时候发货')">📦 发货时间</button>
      <button class="quick-btn" onclick="sendMsg('怎么退换货')">🔄 退换货</button>
      <button class="quick-btn" onclick="sendMsg('手机壳有哪些材质')">🧪 产品材质</button>
      <button class="quick-btn" onclick="sendMsg('支持定制吗')">✏️ 定制款</button>
      <button class="quick-btn" onclick="sendMsg('如何联系人工客服')">📞 人工客服</button>
      <button class="quick-btn" onclick="sendMsg('有什么优惠活动吗')">🎁 优惠活动</button>
    </div>
    <div class="input-row">
      <input type="text" id="userInput" placeholder="请输入您的问题..." onkeydown="if(event.key==='Enter')sendMsg()"/>
      <button onclick="sendMsg()">➤</button>
    </div>
  </div>
</div>
<script>
let history = [];

async function sendMsg(text) {
  const input = document.getElementById("userInput");
  const msg = text || input.value.trim();
  if (!msg) return;
  input.value = "";

  appendMsg("user", msg);
  history.push({role: "user", content: msg});

  const typing = appendTyping();

  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({messages: history})
  });
  const data = await res.json();
  typing.remove();

  const reply = data.reply;
  appendMsg("bot", reply);
  history.push({role: "assistant", content: reply});
}

function appendMsg(role, text) {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = `
    <div class="avatar">${role === "user" ? "👤" : "🤖"}</div>
    <div class="bubble">${text}</div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function appendTyping() {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg bot typing";
  div.style.display = "flex";
  div.innerHTML = `<div class="avatar">🤖</div><div class="bubble">正在输入...</div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "max_tokens": 500,
                "temperature": 0.4
            },
            timeout=30
        )
        reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = "出错了，请稍后再试。"
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
