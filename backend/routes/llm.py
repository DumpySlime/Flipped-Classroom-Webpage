from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from datetime import datetime
import time

# --- Global DB/FS Handlers ---

db = None
fs = None


def init_db(db_instance, fs_instance):
    """Initializes the global database and GridFS connections."""
    global db
    db = db_instance
    global fs
    fs = fs_instance


# --- Configuration & Blueprint Setup ---

llm_bp = Blueprint('llm', __name__)

# DeepSeek AI Configuration (loaded from Flask app config)
DEEPSEEK_API_KEY = None
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


@llm_bp.record_once
def on_load(state):
    """Loads configuration variables from Flask app config."""
    global DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
    app = state.app

    # DeepSeek Configuration
    DEEPSEEK_API_KEY = app.config.get("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = app.config.get("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL)

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


def call_deepseek_api(subject: str, topic: str, instruction: str) -> dict:
    """
    Call DeepSeek API to generate teaching material in JSON format.
    Returns a JSON object with slides structure.
    """
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API key is not configured")

    # Construct the prompt for DeepSeek
    prompt = f"""You are an expert teacher creating educational material.

Subject: {subject}
Topic: {topic}
Additional Instructions: {instruction}

Generate teaching slides in the following JSON format ONLY. Do not include any other text or explanations outside the JSON:

{{
  "slides": [
    {{
      "subtitle": "introduction",
      "content": "- Point 1\\n- Point 2\\n- Point 3",
      "slideType": "explanation",
      "page": 1
    }},
    {{
      "subtitle": "{topic}",
      "content": "- Key concept 1\\n- Key concept 2\\n- Key concept 3",
      "slideType": "explanation",
      "page": 2
    }},
    {{
      "subtitle": "example",
      "content": "Question: [example question]\\nAnswer: [answer]\\nExplanation: [step-by-step explanation]",
      "slideType": "example",
      "page": 3
    }},
    {{
      "subtitle": "conclusion",
      "content": "- Summary point 1\\n- Summary point 2\\n- Practice suggestions",
      "slideType": "explanation",
      "page": 4
    }}
  ]
}}

Generate 4-6 slides appropriate for the topic. Use clear, student-friendly language."""

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
                    "content": "You are an expert educational content creator. You always respond with valid JSON only, no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
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
            "content": f"- Overview of {topic}\n- Why this topic is important in {subject}\n- Learning objectives for this lesson",
            "slideType": "explanation",
            "page": 1,
        },
        {
            "subtitle": topic or "main concept",
            "content": "- Key definitions and terminology\n- Important properties and characteristics\n- Real-world applications and examples",
            "slideType": "explanation",
            "page": 2,
        },
        {
            "subtitle": "example",
            "content": f"Question: Practice problem related to {topic}\nAnswer: Solution to the problem\nExplanation: Step-by-step breakdown of the solution process",
            "slideType": "example",
            "page": 3,
        },
        {
            "subtitle": "conclusion",
            "content": "- Summary of key concepts\n- Common mistakes to avoid\n- Practice exercises and further reading",
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

        data = request.form.to_dict() or request.get_json(silent=True) or {}

        subject = (data.get("subject") or "").strip()
        topic = (data.get("topic") or "").strip()
        instruction = (data.get("instruction") or data.get("description") or "").strip()
        subject_id = (data.get("subject_id") or "").strip()

        if not subject or not topic:
            return jsonify({"error": "Subject and topic are required"}), 400

        print(f"Generating material for: Subject={subject}, Topic={topic}")

        # Try to call DeepSeek AI, fall back to template if API fails
        try:
            material_json = call_deepseek_api(subject, topic, instruction)
            print("Material generated successfully using DeepSeek AI")
        except Exception as e:
            print(f"DeepSeek API failed, using fallback: {e}")
            material_json = build_material_slides_fallback(subject, topic, instruction)

        # Generate a unique SID for this material
        material_sid = f"material_{int(time.time())}_{current_user_id[:8]}"

        # Optionally, save to database for future retrieval
        if db is not None:
            try:
                material_doc = {
                    "sid": material_sid,
                    "subject": subject,
                    "subject_id": subject_id,
                    "topic": topic,
                    "instruction": instruction,
                    "content": material_json,
                    "created_by": current_user_id,
                    "created_at": datetime.utcnow(),
                    "status": "done"
                }
                db.materials.insert_one(material_doc)
                print(f"Material saved to database with sid: {material_sid}")
            except Exception as db_error:
                print(f"Warning: Failed to save material to database: {db_error}")

        response = {
            "code": 0,
            "message": "success",
            "data": {
                "sid": material_sid,
                "materialStatus": "done",
                "material": material_json,
                "subject_id": subject_id,
                "subject": subject,
                "topic": topic,
            },
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error creating material JSON: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


@llm_bp.route('/material/progress', methods=['GET'])
@jwt_required()
def material_progress():
    """
    Progress endpoint for JSON material.
    Since generation is synchronous in material_create, this retrieves saved material by SID.
    """
    try:
        sid = (request.args.get("sid") or "").strip()
        if not sid:
            return jsonify({"error": "sid is required"}), 400

        current_user_id = get_jwt_identity()

        # Try to retrieve from database
        if db is not None:
            material_doc = db.materials.find_one({"sid": sid, "created_by": current_user_id})
            if material_doc:
                return jsonify({
                    "code": 0,
                    "message": "success",
                    "data": {
                        "sid": sid,
                        "materialStatus": material_doc.get("status", "done"),
                        "material": material_doc.get("content"),
                        "subject_id": material_doc.get("subject_id"),
                        "subject": material_doc.get("subject"),
                        "topic": material_doc.get("topic"),
                    }
                }), 200

        # If not found in database, return generic 'done' status
        return jsonify({
            "code": 0,
            "message": "success",
            "data": {
                "sid": sid,
                "materialStatus": "done",
                "material": None
            }
        }), 200

    except Exception as e:
        print(f"Error querying material progress: {e}")
        return jsonify({"error": f"Error querying material progress: {str(e)}"}), 500


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
