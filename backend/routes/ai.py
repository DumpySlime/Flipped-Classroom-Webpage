from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from openai import OpenAI
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import re
import json

ai_bp = Blueprint('ai', __name__)

OPENAI_API_KEY = None
OPENAI_MODEL = None
OPENAI_BASE_URL = None

@ai_bp.record_once
def on_load(state):
    global OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
    app = state.app
    OPENAI_API_KEY = app.config.get("OPENAI_API_KEY")   
    OPENAI_MODEL = app.config.get("OPENAI_MODEL")   
    OPENAI_BASE_URL = app.config.get("OPENAI_BASE_URL")   
    print(f"[OPENAI] API Key loaded: {'YES' if OPENAI_API_KEY else 'NO key in .env'}")

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

    if not OPENAI_API_KEY:
        return jsonify({'error': 'OPENAI_API_KEY missing in .env'}), 400

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
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
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

@ai_bp.route('/generate-question', methods=['POST'])
def generate_question():

    if not OPENAI_API_KEY:
        return jsonify({'error': 'OPENAI_API_KEY missing in .env'}), 400
    
    subject_id = request.form.get('subject_id')
    subject = request.form.get('subject')
    topic = request.form.get('topic')

    #uploaded_by = get_jwt_identity()
    print(f"Generating questions for subject: {subject}, topic: {topic}")
    try:
        system_prompt = {
            "role": "system",
            "content": (f"""
                You are an expert educational content creator. Generate 3 educational questions with detailed solutions on the topic: {topic} of the subject: {subject}.
                
                Requirements:
                - Subject: {subject}
                - Main topic: {topic}
                - Difficulty level: easy
                - Learning objectives: introduction to the topic
                - Question types to include: Multiple Choice and Short Answer
                - Number of questions: 3
                
                For each question, provide:
                1. Clear, well-formulated question text
                2. If multiple choice: 4 options with one correct answer
                3. Detailed step-by-step solution/explanation
                4. Learning objective addressed
                
                Format your response as a JSON object with this structure:
                {{
                    "questions": [
                        {{
                            "questionText": "Question here",
                            "questionType": "multiple_choice" or "short_answer",
                            "options": ["Option 1", "Option 2", "Option 3", "Option 4"], // only for multiple choice
                            "correctAnswer": 1, // index (0-3) for MC, text for short answer
                            "explanation": "Why this is the correct approach and brief reasoning",
                            "stepByStepSolution": "Step 1: First analyze... Step 2: Then calculate... Step 3: Final result...",
                            "learningObjective": "What student learns",
                            "points": 5
                        }}
                    ],
                    "subject": "{subject}",
                    "topic": "{topic}"
                }}
                
                IMPORTANT: For multiple choice questions, correctAnswer must be an index (0, 1, 2, or 3) corresponding to the position in the options array.
                Do NOT include your thinking process, reasoning steps, or any references in the output. Only return the required fields in the specified JSON format.
                Make sure questions are educational, accurate, and appropriate for the beginning level.
                """
            )
        }
        print("setting up OpenAI client...")
        client = OpenAI(
            api_key=OPENAI_API_KEY, 
            base_url=OPENAI_BASE_URL)
        print("Sending request to DeepSeek for question generation...")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                system_prompt
            ],
            stream=False
        )

        print(f"DEEPSEEK response: {response.choices[0].message.content}")
        '''
        payload = {
            "model": OPENAI_MODEL,
            "messages": [system_prompt], 
            "temperature": 1.3,
            "stream": False
        }

        with requests.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            stream=False,
            timeout=90
        ) as resp:
            resp.raise_for_status()
            content = resp.choices[0].message.content
        '''
        return response.choices[0].message.content, 200
    except Exception as e:
        error_msg = "DeepSeek 連線失敗"
        if "402" in str(e): error_msg = "DeepSeek 餘額不足！充值 $1 USD！"
        yield f"data: {json.dumps({'error': error_msg})}\n\n"
        yield "data: [DONE]\n\n"
        return jsonify({'error': str(e)}), 500