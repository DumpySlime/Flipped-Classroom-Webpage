from flask import Blueprint, request, jsonify, Response
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
print(f"[DEEPSEEK] API Key loaded: {'YES' if DEEPSEEK_API_KEY else 'NO key in .env'}")

BAD_KEYWORDS = [
    "answer", "solution"
]

DEFENSIVE_REPLY = (
    "You are being a nasty bad boy. Its a no no for directly giving answers to assignment questions. "
)

def is_assignment_question(message: str) -> bool:
    return any(keyword in message.lower() for keyword in BAD_KEYWORDS)

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def smart_wrap_latex(text: str) -> str:
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('$$') or stripped.startswith('\\('):
            result.append(line)
            continue
        if re.search(r'\\frac|\\times|\\cdot|\^|_|\{|\}', line):
            if stripped.startswith('[') and stripped.endswith(']'):
                line = line.replace('[', '\\(', 1).replace(']', '\\)', 1)
            elif '{' in stripped and '}' in stripped:
                line = re.sub(r'\{([^}]+)\}', r'$$\1$$', line)
        result.append(line)
    return '\n'.join(result)

@ai_bp.route('/ai-chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error': 'No messages'}), 400

    last_user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), '')
    if is_assignment_question(last_user_msg):
        return Response(
        (f"data: {json.dumps({'content': DEFENSIVE_REPLY})}\n\n" +
        "data: [DONE]\n\n"),
        mimetype='text/event-stream'
)

    if not DEEPSEEK_API_KEY:
        return jsonify({'error': 'DEEPSEEK_API_KEY missing in .env'}), 400

    def generate():
        try:
            system_msg = {
                "role": "system",
                "content": (
                    "You are a helpful assistant.Which helps users with their questions. "
                    "However, don't provide any answers related to assignments, homework, exams, or tests. "
                    "You can answer them in traditional chinese(cantonese and easy english). "
                    "ALso if the student ask or request some thing to solve or answer please don't provide answer for them"
                )
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [system_msg, *messages], 
                "temperature": 0.7,
                "stream": True
            }

            with requests.post(
                "https://api.deepseek.com/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                stream=True,
                timeout=90
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').strip()
                        if decoded.startswith("data: "):
                            data = decoded[6:]
                            if data == "[DONE]": continue
                            try:
                                json_data = json.loads(data)
                                delta = json_data['choices'][0]['delta']
                                if 'content' in delta:
                                    content = smart_wrap_latex(delta['content'])
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except: continue
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = "DeepSeek 連線失敗"
            if "402" in str(e): error_msg = "DeepSeek 餘額不足！充值 $1 USD！"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')