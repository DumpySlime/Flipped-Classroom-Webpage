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

    if not DEEPSEEK_API_KEY:
        return jsonify({'error': 'DEEPSEEK_API_KEY missing in .env'}), 400

    session = get_session()

    try:
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "stream": False
        }

        resp = session.post(url, json=payload, headers=headers, timeout=90)
        resp.raise_for_status()
        reply = resp.json()['choices'][0]['message']['content']

        return jsonify({'reply': reply.strip()})

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_msg = "回應太慢，請等耐啲或再試！"
        elif "402" in error_msg:
            error_msg = "DeepSeek 餘額不足！即刻去 https://platform.deepseek.com 充值 $1 USD！"
        print(f"[DeepSeek Error]: {error_msg}")
        return jsonify({'error': error_msg}), 500

    except Exception as e:
        error_msg = f"出錯: {str(e)}"
        print(f"[DeepSeek Error]: {error_msg}")
        return jsonify({'error': error_msg}), 500