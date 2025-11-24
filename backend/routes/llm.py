from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from gridfs import GridFS
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

db = None
fs = None

def init_db(db_instance, fs_instance):
    global db
    db = db_instance
    global fs
    fs = fs_instance

llm_bp = Blueprint('llm', __name__, url_prefix='/api')

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
        # Return generated content to user even if saving fails
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