from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from gridfs import GridFS
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
import base64
import hashlib
import hmac
import time

db = None
fs = None

def init_db(db_instance, fs_instance):
    global db
    db = db_instance
    global fs
    fs = fs_instance

llm_bp = Blueprint('llm', __name__, url_prefix='/api')

XF_PPT_APP_ID = None
XF_PPT_SECRET = None
XF_PPT_BASE_URL = "https://zwapi.xfyun.cn"

@llm_bp.record_once
def on_load(state):
    global XF_PPT_APP_ID, XF_PPT_SECRET, XF_PPT_BASE_URL
    app = state.app
    XF_PPT_APP_ID = app.config.get("XF_PPT_APP_ID")
    XF_PPT_SECRET = app.config.get("XF_PPT_SECRET")
    XF_PPT_BASE_URL = app.config.get("XF_PPT_BASE_URL", XF_PPT_BASE_URL)
    
    print(f"XF PPT AppId loaded: {'YES' if XF_PPT_APP_ID else 'NO XF_PPT_APP_ID'}")
    print(f"XF PPT Base URL: {XF_PPT_BASE_URL}")

# Load AI API configuration from environment variables
DEEPSEEK_API_KEY = None
DEEPSEEK_MODEL = None
DEEPSEEK_BASE_URL = None

@llm_bp.record_once
def on_load(state):
    global DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
    app = state.app
    # Use DEEPSEEK configuration keys
    DEEPSEEK_API_KEY = app.config.get("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL = app.config.get("DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL = app.config.get("DEEPSEEK_BASE_URL")
    
    print(f"DeepSeek API Key loaded: {'YES' if DEEPSEEK_API_KEY else 'NO key in .env'}")
    print(f"Using DeepSeek model: {DEEPSEEK_MODEL}")
    print(f"Using DeepSeek base URL: {DEEPSEEK_BASE_URL}")

# Custom retry logic for API calls
def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 429), # Add 429 for rate limiting
    session=None,
):
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

def xf_ppt_headers():
    """
    Construct PPTv2 authentication header
    Headers must include: appId, timestamp(seconds), signature
    """
    if not XF_PPT_APP_ID or not XF_PPT_SECRET:
        raise Exception("XF PPTv2 is not configured (XF_PPT_APP_ID / XF_PPT_SECRET missing)")

    ts = int(time.time())  
    md5_text = hashlib.md5(f"{XF_PPT_APP_ID}{ts}".encode("utf-8")).hexdigest()
    raw_hmac = hmac.new(
        XF_PPT_SECRET.encode("utf-8"),
        md5_text.encode("utf-8"),
        hashlib.sha1
    ).digest()
    signature = base64.b64encode(raw_hmac).decode("utf-8")

    return {
        "appId": XF_PPT_APP_ID,
        "timestamp": str(ts),
        "signature": signature,
    }


def xf_post_multipart(path: str, data: dict | None = None, files: dict | None = None):
    """
    Call zwapi.xfyun.cn multipart/form-data interface
    Used for /api/ppt/v2/create
    """
    if data is None:
        data = {}

    session = get_session()
    headers = xf_ppt_headers() 
    url = f"{XF_PPT_BASE_URL}{path}"

    resp = session.post(url, data=data, files=files, headers=headers, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    # Simple logging for debugging
    if result.get("code") not in (0, None) or not result.get("flag", True):
        print(f"XF PPT create API warning: {result}")

    return result


def xf_get(path: str, params: dict):
    """
    Call zwapi.xfyun.cn GET interface
    Used for /api/ppt/v2/progress
    """
    session = get_session()
    headers = xf_ppt_headers()
    url = f"{XF_PPT_BASE_URL}{path}"

    resp = session.get(url, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

@llm_bp.route('/ppt/create', methods=['POST'])
@jwt_required()
def ppt_create():
    """
    Interface for generating PPT
    Documentation: POST https://zwapi.xfyun.cn/api/ppt/v2/create
    """
    print("Received PPT create request")

    try:
        current_user_id = get_jwt_identity()
        print(f"PPT create request from user: {current_user_id}")

        data = request.get_json(silent=True) or request.form.to_dict() or {}

        # Get parameters from frontend
        subject = (data.get("subject") or "").strip()
        topic = (data.get("topic") or "").strip()
        instruction = (data.get("instruction") or data.get("description") or "").strip()
        
        # Construct query content
        query_parts = []
        if subject:
            query_parts.append(f"Subject: {subject}")
        if topic:
            query_parts.append(f"Topic: {topic}")
        if instruction:
            query_parts.append(f"Additional instructions: {instruction}")
        
        query = (data.get("query") or "").strip()
        if not query and query_parts:
            query = ". ".join(query_parts)
        template_id = (data.get("templateId") or "").strip()
        author = (data.get("author") or "").strip() or "SmartDoc" 
        language = (data.get("language") or "en").strip()      # Default to English

        if not query:
            return jsonify({"error": "Subject and topic are required"}), 400

      
        form = {
            "query": query,
            "language": language,
            "author": author,
        }
        if template_id:
            form["templateId"] = template_id

        print(f"Calling XF PPT create with form: {form}")

        try:
            result = xf_post_multipart("/api/ppt/v2/create", data=form)
        except Exception as e:
            error_str = str(e)
            if "402" in error_str:
                return jsonify({"error": "XF balance insufficient! Please recharge $1 USD!"}), 402
            raise e

        
        # Save PPT to database
        if result.get("code") == 0 and result.get("data", {}).get("sid"):
            save_ppt_task(current_user_id, result["data"]["sid"], subject, topic, instruction, template_id, author, language)
        
        return jsonify(result), 200

    except Exception as e:
        print(f"Error creating PPT: {e}")
        error_str = str(e)
        if "402" in error_str:
            return jsonify({"error": "XF 餘額不足！充值 $1 USD！"}), 402
        return jsonify({"error": error_str}), 500


@llm_bp.route('/ppt/progress', methods=['GET'])
@jwt_required()
def ppt_progress():
    """
    Interface for querying PPT generation progress & retrieving pptUrl
    Documentation: GET https://zwapi.xfyun.cn/api/ppt/v2/progress?sid={}
    """
    sid = (request.args.get("sid") or "").strip()
    if not sid:
        return jsonify({"error": "sid is required"}), 400

    current_user_id = get_jwt_identity()
    print(f"Query PPT progress, sid={sid} for user: {current_user_id}")

    try:
        result = xf_get("/api/ppt/v2/progress", params={"sid": sid})

    
        # data.pptUrl is the PPT download link (valid for 30 days)
        # when PPT generation is complete, download and save to database
        if result.get("code") == 0 and result.get("data", {}).get("pptStatus") == "done" and result.get("data", {}).get("pptUrl"):
            ppt_url = result["data"]["pptUrl"]
            
            # Query PPT task information to get subject and topic
            ppt_task = db.ppt_tasks.find_one({"sid": sid, "created_by": current_user_id})
            if ppt_task:
                subject = ppt_task.get("subject", "Unknown")
                topic = ppt_task.get("topic", "Unknown")
                
                # Generate filename
                safe_topic = "".join(c if c.isalnum() or c in '_-' else '_' for c in topic)
                if not safe_topic:
                    safe_topic = "untitled"
                filename = f"{safe_topic[:50]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pptx"
                
                print(f"PPT generation completed, attempting to save file: {filename}")
                # Save to GridFS and create record in materials collection
                material_id = save_ppt_file_to_db(current_user_id, subject, topic, ppt_url, filename)
                
                if material_id:
                    db.ppt_tasks.update_one(
                        {"_id": ppt_task["_id"]},
                        {"$set": {"status": "done", "saved_material_id": material_id}}
                    )
                    print(f"PPT task updated with material reference: {ppt_task['_id']}")

        return jsonify(result), 200

    except Exception as e:
        print(f"Error querying PPT progress: {e}")
        return jsonify({"error": str(e)}), 500


def save_material_to_db(subject, topic, content, user_id):
    """Save generated material to database"""
    print(f"Attempting to save generated material to database")
    
def generate_llm_content(subject, topic, instruction, user_id):
    """
    Generates content using the DeepSeek LLM API.
    """
    if not DEEPSEEK_API_KEY or not DEEPSEEK_MODEL:
        return {"error": "DeepSeek API keys or model configuration is missing."}, 500

    # 1. Construct the System Prompt
    system_prompt = (
        "You are an expert educational content generator. "
        "Your task is to create high-quality, engaging, and comprehensive study material "
        "on the requested topic. Format the response clearly using Markdown. "
        "The content should be suitable for a flipped classroom model. "
        "Include an introduction, several key sub-sections, and a brief conclusion. "
    )

    # 2. Construct the User Prompt
    user_prompt = f"Generate study material on the subject '{subject}' for the topic '{topic}'. "
    if instruction:
        user_prompt += f"Specific instructions: {instruction}"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    api_url = DEEPSEEK_BASE_URL if DEEPSEEK_BASE_URL else "https://api.deepseek.com/v1/chat/completions"

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "stream": False
    }

    try:
        print(f"Attempting to call DeepSeek API at: {api_url}")
        session = requests_retry_session()
        response = session.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        
        if data and data.get('choices'):
            content = data['choices'][0]['message']['content']
            return {"content": content}, 200
        else:
            error_message = data.get('error', {}).get('message', 'Unknown DeepSeek API error.')
            print(f"DeepSeek API error: {error_message}")
            return {"error": f"LLM content generation failed: {error_message}"}, 500

    except requests.exceptions.RequestException as e:
        print(f"API Request failed after retries: {str(e)}")
        return {"error": f"LLM service connection error: {str(e)}"}, 503
    except Exception as e:
        print(f"An unexpected error occurred during LLM call: {str(e)}")
        return {"error": f"Internal server error: {str(e)}"}, 500


def save_generated_material(subject, topic, content, user_id):
    """
    Saves the generated content to the MongoDB 'materials' collection.
    Returns the inserted document ID or None on failure.
    """
    try:
        if not db:
            raise Exception("Database not initialized.")
            
        safe_topic = topic.replace(' ', '_').replace('/', '-').replace('\\', '-')
        
        safe_topic = "".join(c if c.isalnum() or c in '_-' else '_' for c in topic)
        if not safe_topic:
            safe_topic = "untitled"
        
        # Find subject_id 
        subject_id = None
        try:
            subject_doc = db.subjects.find_one({"subject": subject})
            if subject_doc and "_id" in subject_doc:
                subject_id = subject_doc["_id"]
        except Exception as db_err:
            print(f"Warning: Error finding subject in database: {str(db_err)}")
        
        # Create material document
        material_doc = {
            "subject": subject,
            "topic": topic,
            "content": content,
            "uploaded_by": user_id,
            "upload_date": datetime.utcnow(),
            "type": "generated",
            "filename": f"{safe_topic[:50]}_generated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
        }
        
        # Insert into database
        result = db.materials.insert_one(material_doc)
        print(f"Material successfully saved to database with ID: {result.inserted_id}")
        return result.inserted_id
        
    except Exception as e:
        print(f"Error saving material to database: {str(e)}")
        return None
        

def save_ppt_task(user_id, sid, subject, topic, instruction, template_id, author, language):
    """Save PPT task information to database"""
    print(f"Attempting to save PPT task to database: {sid}")
    
    try:
        # Validate database connection
        if not db:
            print("Warning: Database not initialized, cannot save PPT task")
            return None
        
        # Create PPT task document
        ppt_task_doc = {
            "sid": sid,
            "subject": subject,
            "topic": topic,
            "instruction": instruction,
            "template_id": template_id,
            "author": author,
            "language": language,
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        # Insert into database
        result = db.ppt_tasks.insert_one(ppt_task_doc)
        print(f"PPT task successfully saved to database with ID: {result.inserted_id}")
        return result.inserted_id
        
    except Exception as e:
        print(f"Error saving PPT task to database: {str(e)}")
        return None


def save_ppt_file_to_db(user_id, subject, topic, ppt_url, filename="simpleppt.pptx"):
    """Download and save PPT file to MongoDB GridFS and create record only in materials collection"""
    print(f"Attempting to download and save PPT file from: {ppt_url}")
    
    try:
        # Validate database and GridFS connection
        if not db or not fs:
            print("Warning: Database or GridFS not initialized, cannot save PPT file")
            return None
        
        # Download PPT file
        session = get_session()
        response = session.get(ppt_url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Save to GridFS
        file_id = fs.put(
            response.raw,
            filename=filename,
            content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            upload_date=datetime.utcnow()
        )
        
        # Find corresponding subject_id
        subject_id = None
        try:
            subject_doc = db.subjects.find_one({"subject": subject})
            if subject_doc and "_id" in subject_doc:
                subject_id = subject_doc["_id"]
        except Exception as db_err:
            print(f"Warning: Error finding subject in database: {str(db_err)}")
        
        # Create material document for materials collection
        material_doc = {
            "subject": subject,
            "subject_id": subject_id,
            "topic": topic,
            "content": f"PPT presentation: {topic}",
            "uploaded_by": user_id,
            "upload_date": datetime.utcnow(),
            "type": "ppt",
            "filename": filename,
            "file_id": file_id,  # Reference to the GridFS file
            "size_bytes": response.headers.get('content-length', 0)
        }
        
        # Insert to materials collection
        material_result = db.materials.insert_one(material_doc)
        print(f"PPT file successfully saved to materials collection with ID: {material_result.inserted_id}")
        
        # Return the materials collection ID
        return material_result.inserted_id
        
    except Exception as e:
        print(f"Error saving PPT file to database: {str(e)}")
        return None

# Add a GET endpoint for testing
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
            "message": "This is a GET endpoint for testing. Please use POST for actual material generation.",
            "received_params": {"subject": subject, "topic": topic, "instruction": instruction}
        }), 200
    except Exception as e:
        print(f"Error in llm_query_get: {str(e)}")
        return jsonify({"error": "An internal error occurred."}), 500

# Line 161 - the start of the next route (where the original error pointed)
@llm_bp.route('/llm/generate', methods=['POST']) 
@jwt_required()
def llm_generate():
    """
    Receives request to generate new learning material using the LLM.
    Requires subject, topic, and an optional instruction.
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    subject = data.get('subject')
    topic = data.get('topic')
    instruction = data.get('instruction')

    if not subject or not topic:
        return jsonify({"error": "Subject and topic are required."}), 400

    # 1. Generate Content
    result, status_code = generate_llm_content(subject, topic, instruction, user_id)
    
    if status_code != 200:
        return jsonify(result), status_code

    generated_content = result.get('content')
    
    # 2. Save to DB (optional, runs in background)
    saved_id = save_generated_material(subject, topic, generated_content, user_id)
    
    # 3. Return the generated content to the user
    return jsonify({
        "message": "Content generated successfully.",
        "content": generated_content,
        "material_id": str(saved_id) if saved_id else None
    }), 200