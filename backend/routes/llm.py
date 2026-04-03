from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import ast

# --- Global DB Handlers ---

db = None


def init_db(db_instance):
    """Initializes the global database connections."""
    global db
    db = db_instance

# --- Configuration & Blueprint Setup ---

llm_bp = Blueprint('llm', __name__)

# DeepSeek AI Configuration (loaded from Flask app config)
DEEPSEEK_API_KEY = None
DEEPSEEK_BASE_URL = None


@llm_bp.record_once
def on_load(state):
    """Loads configuration variables from Flask app config."""
    global DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
    app = state.app

    # DeepSeek Configuration
    DEEPSEEK_API_KEY = app.config.get("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = app.config.get("DEEPSEEK_BASE_URL")

    print(f"DeepSeek API Key loaded: {'YES' if DEEPSEEK_API_KEY else 'NO'}")
    print(f"DeepSeek Base URL: {DEEPSEEK_BASE_URL}")


# --- Utility Functions ---


def get_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 429),
    session=None,
) -> requests.Session:
    """Custom retry logic for API calls."""
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


# --- DeepSeek AI Helper Functions ---


def call_deepseek_api(subject: str, topic: str, subtopic: list, form: str, instruction: str, language: str) -> dict:
    """
    Call DeepSeek API to generate teaching material in JSON format.
    Returns a JSON object with slides structure.
    """
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API key is not configured")

    # Construct the prompt for DeepSeek
    user_prompt = f"""Create teaching slides for a Hong Kong secondary school student.

Requirements:
- Subject: {subject}
- Topic: {topic}
- Subtopics: {', '.join(subtopic) if subtopic else 'None'}
- Secondary Year: {form}
- Additional Instructions: {instruction if instruction else 'None'}

Instructions:
- Generate 4 to 10 slides depending on the complexity of the topic.
- Use clear, concise, student-friendly language suitable for the specified secondary year.
- If subtopics are provided, make sure the slides cover them naturally.
- Include explanation slides and at least 1 worked example slide when appropriate.
- Keep each slide focused on one main idea.
- Avoid generic placeholder text.
"""
    system_prompt = f"""
You are a expert HKDSE educational content creator.

You must return valid JSON only.
Do not translate JSON keys.
Keep the JSON structure exactly as shown.
Only translate the educational text content.
Specifically:
- "subtitle" values must be in {language}
- each string inside "content" must be in {language}
- keys such as "slides", "subtitle", "content", "slideType", and "page" must remain exactly in English
- values of "slideType" must remain exactly "explanation" or "example"

Generate teaching slides in the following JSON format:

{{
  "slides": [
    {{
      "subtitle": "introduction",
      "content": ["Point 1", "Point 2", "Point 3"],
      "slideType": "explanation",
      "page": 1
    }},
    {{
      "subtitle": "{subtopic[0] if subtopic else topic}",
      "content": ["Key concept 1", "Key concept 2", "Key concept 3"],
      "slideType": "explanation",
      "page": 2
    }},
    {{
      "subtitle": "example",
      "content": ["Question: [example question]", "Answer: [answer]", "Explanation: [step-by-step explanation]"],
      "slideType": "example",
      "page": 3
    }},
    {{
      "subtitle": "conclusion",
      "content": ["Summary point 1", "Summary point 2", "Practice suggestions"],
      "slideType": "explanation",
      "page": 4
    }}
  ]
}}
"""

    try:
        session = get_session()
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }

        print(f"Calling DeepSeek API for topic: {topic}")
        response = session.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        
        # Extract the JSON content from DeepSeek response
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Parse the JSON content
        import json
        slides_data = json.loads(content)
        
        print(f"DeepSeek API call successful")
        return slides_data

    except requests.exceptions.HTTPError as e:
        print(f"DeepSeek API HTTP Error: {e}")
        raise Exception(f"DeepSeek API error: {str(e)}")
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        raise Exception(f"Failed to generate material: {str(e)}")


def build_material_slides_fallback(subject: str, topic: str, instruction: str) -> dict:
    """
    Fallback helper that returns a JSON-only slides structure.
    Used when DeepSeek API is unavailable or for testing.
    """
    slides = [
        {
            "subtitle": "introduction",
            "content": [f"Overview of {topic}", f"Why this topic is important in {subject}", f"Learning objectives for this lesson"],
            "slideType": "explanation",
            "page": 1,
        },
        {
            "subtitle": topic or "main concept",
            "content": ["Key definitions and terminology", "Important properties and characteristics", "Real-world applications and examples"],
            "slideType": "explanation",
            "page": 2,
        },
        {
            "subtitle": "example",
            "content": [f"Question: Practice problem related to {topic}", f"Answer: Solution to the problem", f"Explanation: Step-by-step breakdown of the solution process"],
            "slideType": "example",
            "page": 3,
        },
        {
            "subtitle": "conclusion",
            "content": ["Summary of key concepts", "Common mistakes to avoid", "Practice exercises and further reading"],
            "slideType": "explanation",
            "page": 4,
        },
    ]
    
    if instruction:
        slides.append({
            "subtitle": "additional notes",
            "content": f"Special instructions: {instruction}",
            "slideType": "explanation",
            "page": 5,
        })
    
    return {"slides": slides}


# --- Material JSON Endpoints (DeepSeek AI) ---


@llm_bp.route('/material/create', methods=['POST'])
@jwt_required()
def material_create():
    """
    Endpoint for generating JSON-only teaching material using DeepSeek AI.
    Returns a JSON 'slides' object.
    """
    try:
        current_user_id = get_jwt_identity()
        print(f"Material create request from user: {current_user_id}")

        data = request.form

        subject = (data.get("subject") or "").strip()
        topic = (data.get("topic") or "").strip()
        instruction = (data.get("description") or data.get("instruction") or "").strip()
        subject_id = (data.get("subject_id") or "").strip()
        
        language = (data.get("language") or "").strip()
        raw_subtopic = (data.get("sub_topics") or "")
        form = (data.get("form") or "").strip()

        # update raw_subtopic from string to array
        subtopic = ast.literal_eval(raw_subtopic) if isinstance(raw_subtopic, str) else raw_subtopic

        if not subject or not topic:
            return jsonify({"error": "Subject and topic are required"}), 400

        # Prepare to save material sets into /db/material-add

        try:
            base = request.host_url.rstrip('/')
            auth_hdr = {}
            auth = request.headers.get("Authorization")
            if auth:
                auth_hdr["Authorization"] = auth
            
            session = get_session()
            url = f"{base}/db/material-add"

            print(f"Preparing to post material via /db/material-add route at {url}")
        except Exception as e:
            raise Exception(f"Error preparing url: {str(e)}")
        
        # Initialize material object first
        # Make the POST request through /db/material-add
        try:
            # Prepare file object
            data = {
                "subject_id": subject_id,
                "topic": topic,
                "slides": [],
                "create_type": "generated",
                "status": "generating",
                "language": language,
                "subtopic": raw_subtopic,
                "form": form,
            }
            print(f"Posting initial material record with data: {data}")
            resp = session.post(
                url,
                data=data,
                headers=auth_hdr,
                timeout=30
            )
            resp.raise_for_status()
            material_result = resp.json()

            print(f"Material successfully posted via /db/material-add: {material_result}")

        except Exception as e:
            raise Exception(f"Failed to save material via /db/material-add route: {str(e)}")

        # Try to call DeepSeek AI, fall back to template if API fails
        try:
            material_json = call_deepseek_api(subject, topic, subtopic, form, instruction, language)
            print("Material generated successfully using DeepSeek AI")
            print(f"Material JSON: {material_json}")
        except Exception as e:
            print(f"DeepSeek API failed, using fallback: {e}")
            material_json = build_material_slides_fallback(subject, topic, instruction)

        """
        For now we do synchronous generation - directly update the material record
        since the user is waiting for the response.
        """

        # Update the material in the database with the generated content
        # Make the PUT request through /db/material-update
        material_sid = material_result.get("material_id", "")
        url = f"{base}/db/material-update?material_id={material_sid}"
        try:
            update_data = {
                "slides": material_json,
                "status": "completed",
            }

            resp = session.put(
                url,
                json=update_data,
                headers=auth_hdr,
                timeout=30
            )
            resp.raise_for_status()
            updated_result = resp.json()

            print(f"Material successfully updated via /db/material-update: {updated_result}")

        except Exception as e:
            raise Exception(f"Failed to update material via /db/material-update route: {str(e)}")

        response = {
            "code": 0,
            "message": "success",
            "data": {
                "sid": material_sid,
                "status": "done",
                "slides": material_json,
                "subject_id": subject_id,
                "subject": subject,
                'attribute': {
                    "topic": topic,
                    "subtopic": subtopic,
                    "form": form,
                    "language": language
                },
                "created_at": material_result.get("created_at"),
            },
        }
        return jsonify(response), 200

    except Exception as e:
        print(f"Error creating material JSON: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# --- Test/Debug Endpoints ---


@llm_bp.route('/test/material', methods=['POST'])
@jwt_required()
def test_material():
    """Test endpoint to verify DeepSeek API integration"""
    try:
        print("=== Testing DeepSeek AI Integration ===")
        
        data = request.get_json() or {}
        subject = data.get("subject", "Mathematics")
        topic = data.get("topic", "Pythagorean Theorem")
        instruction = data.get("instruction", "")

        # Call DeepSeek API
        result = call_deepseek_api(subject, topic, instruction)
        
        return jsonify({
            "status": "success",
            "message": "DeepSeek AI is working",
            "result": result
        }), 200

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@llm_bp.route('/llm/query', methods=['GET'])
@jwt_required()
def llm_query_get():
    """GET method compatibility endpoint for testing"""
    try:
        subject = request.args.get('subject')
        topic = request.args.get('topic')
        instruction = request.args.get('instruction')

        if not subject or not topic:
            return jsonify({"error": "Subject and topic are required parameters"}), 400

        return jsonify({
            "message": "This is a GET endpoint for testing. Please use POST /api/llm/material/create for actual material generation.",
            "received_params": {
                "subject": subject,
                "topic": topic,
                "instruction": instruction
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
