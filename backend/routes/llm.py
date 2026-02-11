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
      "content": ["Point 1", "Point 2", "Point 3"],
      "slideType": "explanation",
      "page": 1
    }},
    {{
      "subtitle": "{topic}",
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

        data = request.form.to_dict() or request.get_json(silent=True) or {}

        subject = (data.get("subject") or "").strip()
        topic = (data.get("topic") or "").strip()
        instruction = (data.get("instruction") or data.get("description") or "").strip()
        subject_id = (data.get("subject_id") or "").strip()
        
        if not subject or not topic:
            return jsonify({"error": "Subject and topic are required"}), 400

        print(f"Generating material for: Subject={subject}, Topic={topic}")
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
            print(f"Topic: {topic}")
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
            }

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
            material_json = call_deepseek_api(subject, topic, instruction)
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
                "topic": topic,
                "created_at": material_result.get("created_at"),
            },
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error creating material JSON: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

'''
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
                        "status": material_doc.get("status", "done"),
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
                "status": "done",
                "material": None
            }
        }), 200

    except Exception as e:
        print(f"Error querying material progress: {e}")
        return jsonify({"error": f"Error querying material progress: {str(e)}"}), 500
'''

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
