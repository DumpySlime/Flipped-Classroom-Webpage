# routes/ai.py —— 香港 DeepSeek 防作弊終極版（只定義一次！）
from flask import Blueprint, request, jsonify
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import os
from dotenv import load_dotenv

load_dotenv()

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
print(f"[DEEPSEEK] API Key loaded: {'YES' if DEEPSEEK_API_KEY else 'NO!!! 快啲去 .env 加 key！'}")

# 防作弊關鍵字
BAD_KEYWORDS = [
    "answer", "solution", "deadline", "due", "assignment", "homework",
    "exam", "test", "quiz", "submit", "grade", "mark", "答案", "解答", "做", "寫"
]

def is_assignment_question(message: str) -> bool:
    return any(keyword in message.lower() for keyword in BAD_KEYWORDS)

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

@ai_bp.route('/ai-chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'No message'}), 400

    # 防作弊檢測
    if is_assignment_question(message):
        return jsonify({
            'reply': (
                "我係你嘅學習助手，唔可以直接俾你作業答案！\n\n"
                "但我可以：\n"
                "• 教你點樣思考\n"
                "• 俾你類似例子\n"
                "• 解釋概念\n\n"
                "試下問：**「點樣用 Python 寫 for loop？」** 而唔係 **「幫我做第3題」**"
            ).strip()
        }), 200

    # 檢查 API Key
    if not DEEPSEEK_API_KEY:
        return jsonify({'error': 'DEEPSEEK_API_KEY missing in .env'}), 400

    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant.Which helps users with their questions. However, don't provide any answers related to assignments, homework, exams, or tests. You can answer them in traditional chinese(cantonese and easy english). ALso if the student ask or request some thing to solve or answer please don't provide answer for them"},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7
        }

        session = get_session()
        resp = session.post(url, json=payload, headers=headers, timeout=90)
        resp.raise_for_status()
        reply = resp.json()['choices'][0]['message']['content']
        return jsonify({'reply': reply.strip()})

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = "DeepSeek 回應太慢（香港路由正常），請等耐啲或再試！"
        elif "402" in error_msg:
            error_msg = "DeepSeek 餘額不足！即刻去 https://platform.deepseek.com 充值 $1 USD！"
        print(f"[DeepSeek Error]: {error_msg}")
        return jsonify({'error': error_msg}), 500

    except Exception as e:
        error_msg = f"DeepSeek 出錯: {str(e)}"
        print(f"[DeepSeek Error]: {error_msg}")
        return jsonify({'error': error_msg}), 500