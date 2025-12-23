from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import re
import json

ai_bp = Blueprint('ai', __name__)

DEEPSEEK_API_KEY = None
DEEPSEEK_MODEL = None
DEEPSEEK_BASE_URL = None

@ai_bp.record_once
def on_load(state):
    global DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
    app = state.app
    DEEPSEEK_API_KEY = app.config.get("DEEPSEEK_API_KEY")   
    DEEPSEEK_MODEL = app.config.get("DEEPSEEK_MODEL")   
    DEEPSEEK_BASE_URL = app.config.get("DEEPSEEK_BASE_URL")   
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

@ai_bp.route('/generate-question', methods=['POST'])
@jwt_required()
def generate_question():

    if not DEEPSEEK_API_KEY:
        return jsonify({'error': 'DEEPSEEK_API_KEY missing in .env'}), 400

    topic = request.form.get('topic')
    material_id = request.form.get('material_id')

    print(f"Content-Type: {request.content_type}")
    print(f"Form fields: {dict(request.form)}")
    print(f"material_id from form: '{request.form.get('material_id')}'")

    if not material_id or not topic:
        return jsonify({'error': 'material_id and topic are required'}), 400

    uploaded_by = get_jwt_identity()
    print(f"Generating questions for material:{material_id} , topic: {topic}")

    content = None
    
    try:
        system_prompt = {
            "role": "system",
            "content": f'''
                You are an expert educational content creator.

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
                    "topic": "{{topic}}"
                }}

                IMPORTANT: For multiple choice questions, correctAnswer must be an index (0, 1, 2, or 3) corresponding to the position in the options array.
                Do NOT include your thinking process, reasoning steps, or any references in the output. Only return the required fields in the specified JSON format.
                Make sure questions are educational, accurate, and appropriate for the beginning level.
                '''
        }

        user_prompt = {
            "role": "user",
            "content": f'''
                Generate 3 educational questions with detailed solutions on the topic: {topic}.
                
                Requirements:
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
                '''
        }

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [system_prompt, user_prompt], 
            "temperature": 1.3,
            "stream": False
        }

        with requests.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            stream=False,
            timeout=90
        ) as resp:
            resp.raise_for_status()
            response = resp.json()
            content = response['choices'][0]['message']['content']
            print(f"Questions generated successfully: {content}")
            # Parse content as JSON
            try:
                if content.startswith("```"):
                    content = content[len("```json"):].strip()
                if content.endswith("```"):
                    content = content[:-len("```")].strip()
                content_json = json.loads(content)
            except json.JSONDecodeError as jde:
                print(f"JSON decode error: {str(jde)}")
                return jsonify({'error': 'Failed to parse generated content as JSON', 'details': str(jde)}), 500
            
        # Prepare to save question sets into /db/question-add
        try:
            base = request.host_url.rstrip('/')
            auth_hdr = {}
            auth = request.headers.get("Authorization")
            if auth:
                auth_hdr["Authorization"] = auth
            
            session = get_session()
            url = f"{base}/db/question-add"

            print(f"Preparing to post questions via /db/question-add route at {url}")
            print(f"Topic: {topic}, User ID: {uploaded_by}")
        except Exception as e:
            raise Exception(f"Error preparing url: {str(e)}")

        
        # Make the POST request through /db/question-add
        try:
            # Prepare file object
            data = {
                "material_id": str(material_id) if material_id else "",
                # "topic": topic,
                "user_id": uploaded_by,
                "question_content": content_json,
                "create_type": "generated"
            }

            resp = session.post(
                url,
                json=data,
                headers=auth_hdr,
                timeout=30
            )
            resp.raise_for_status()
            question_result = resp.json()

            print(f"Material successfully posted via /db/question-add: {question_result}")

            return question_result
        except Exception as e:
            raise Exception(f"Failed to save questions via /db/question-add route: {str(e)}")

    except Exception as e:
        error_msg = "DeepSeek 連線失敗"
        if "402" in str(e): 
            error_msg = "DeepSeek 餘額不足！充值 $1 USD！"
        return jsonify({'error': error_msg, 'details': str(e)}), 500
    