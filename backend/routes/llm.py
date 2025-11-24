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
OPENAI_API_KEY = None
OPENAI_MODEL = None
OPENAI_BASE_URL = None

@llm_bp.record_once
def on_load(state):
    global OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
    app = state.app
    OPENAI_API_KEY = app.config.get("OPENAI_API_KEY")
    OPENAI_MODEL = app.config.get("OPENAI_MODEL")
    OPENAI_BASE_URL = app.config.get("OPENAI_BASE_URL")
    
    print(f"API Key loaded: {'YES' if OPENAI_API_KEY else 'NO key in .env'}")
    print(f"Using model: {OPENAI_MODEL}")
    print(f"Using base URL: {OPENAI_BASE_URL}")

def get_session():
    """Create a requests session with retry mechanism"""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

@llm_bp.route('/llm/query', methods=['POST'])
@jwt_required()
def llm_query():
    """API endpoint for generating teaching materials"""
    # Log request start
    print(f"Received material generation request")
    
    try:
        # Get current user information
        current_user_id = get_jwt_identity()
        print(f"Request from user: {current_user_id}")
        
        # Get data from request body
        data = request.get_json()
        if not data:
            print(f"Error: No JSON data provided in request")
            return jsonify({"error": "No data provided in request body"}), 400
        
        # Extract and validate parameters - handle different formats from frontend
        subject = data.get('subject')
        if isinstance(subject, list) and subject:
            subject = subject[0]
        elif not subject:
            subject = ''
        
        topic = data.get('topic')
        if isinstance(topic, list) and topic:
            topic = topic[0]
        elif not topic:
            topic = ''
        
        instruction = data.get('instruction', '')
        if isinstance(instruction, list) and instruction:
            instruction = instruction[0]
        
        # Detailed input validation
        if not subject or not subject.strip():
            print(f"Error: Empty or invalid subject provided")
            return jsonify({"error": "Subject is required and cannot be empty"}), 400
            
        if not topic or not topic.strip():
            print(f"Error: Empty or invalid topic provided")
            return jsonify({"error": "Topic is required and cannot be empty"}), 400
            
        # Validate input length to prevent excessively long inputs
        if len(subject) > 100:
            print(f"Error: Subject too long ({len(subject)} characters)")
            return jsonify({"error": "Subject too long (maximum 100 characters)"}), 400
            
        if len(topic) > 200:
            print(f"Error: Topic too long ({len(topic)} characters)")
            return jsonify({"error": "Topic too long (maximum 200 characters)"}), 400
            
        if instruction and len(instruction) > 1000:
            print(f"Error: Instruction too long ({len(instruction)} characters)")
            return jsonify({"error": "Instruction too long (maximum 1000 characters)"}), 400
        
        # Check if API key exists
        if not OPENAI_API_KEY:
            print(f"Error: OPENAI_API_KEY not found in environment variables")
            return jsonify({"error": "AI service is not configured properly. Please contact administrator."}), 500
        
        # Prepare AI prompt
        prompt = generate_material_prompt(subject, topic, instruction)
        
        # Call Deepseek API to generate material
        material_content = generate_content_with_ai(prompt)
        
        # Save generated material to database
        material_id = save_material_to_db(subject, topic, material_content, current_user_id)
        
        return jsonify({
            "success": True,
            "material_id": str(material_id),
            "content": material_content,
            "subject": subject,
            "topic": topic
        }), 200
        
    except Exception as e:
        print(f"Error generating material: {str(e)}")
        return jsonify({"error": str(e)}), 500



def generate_material_prompt(subject, topic, instruction):
    """Generate AI prompt for creating teaching materials"""
    base_prompt = f"""
    You are an expert teacher in {subject}. Create comprehensive teaching material about "{topic}".
    Include the following sections:
    1. Introduction to the topic
    2. Key concepts
    3. Examples
    4. Practice questions
    5. Summary
    
    Format the material in markdown with proper headings, bullet points, and code blocks where appropriate.
    Make the content educational, clear, and suitable for students.
    """
    
    if instruction:
        base_prompt += f"\n\nAdditional instructions: {instruction}"
    
    return base_prompt

def generate_content_with_ai(prompt):
    """Call Deepseek API to generate content"""
    print("Calling Deepseek API to generate content...")
    
    try:
        session = get_session()
        
        system_msg = {
            "role": "system",
            "content": "You are a helpful assistant that creates high-quality educational materials. Format your response in markdown."
        }
        
        user_msg = {
            "role": "user",
            "content": prompt
        }
        
        payload = {
            "model": OPENAI_MODEL,
            "messages": [system_msg, user_msg],
            "temperature": 0.7,
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Add request timeout handling
        try:
            # Build the complete API endpoint URL
            api_endpoint = f"{OPENAI_BASE_URL}/chat/completions"
            response = session.post(
                api_endpoint,
                json=payload,
                headers=headers,
                timeout=60
            )
        except requests.exceptions.Timeout:
            print("Error: Deepseek API request timed out")
            raise Exception("AI service took too long to respond. Please try again later.")
        except requests.exceptions.ConnectionError:
            print("Error: Connection error to Deepseek API")
            raise Exception("Failed to connect to AI service. Please check your internet connection.")
        
        # Check response status code
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            error_message = str(http_err)
            print(f"Error: HTTP error from Deepseek API: {error_message}")
            if response.status_code == 402:
                raise Exception("AI service quota exceeded. Please contact administrator to recharge.")
            elif response.status_code == 401:
                raise Exception("AI service authentication failed. Please contact administrator.")
            elif response.status_code >= 500:
                raise Exception("AI service is currently unavailable. Please try again later.")
            else:
                raise Exception(f"AI service error: {error_message}")
        
        # Parse response content
        try:
            result = response.json()
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from Deepseek API")
            raise Exception("Received invalid response from AI service. Please try again.")
        
        # Validate response structure
        if 'choices' not in result or not result['choices']:
            print("Error: Unexpected response structure from Deepseek API")
            raise Exception("Received incomplete response from AI service. Please try again.")
            
        if 'message' not in result['choices'][0] or 'content' not in result['choices'][0]['message']:
            print("Error: Missing content in Deepseek API response")
            raise Exception("No content generated by AI service. Please try again.")
        
        content = result['choices'][0]['message']['content']
        print(f"Content successfully generated (length: {len(content)} characters)")
        return content
        
    except Exception as e:
        if "AI service" in str(e):
            # Specific errors already handled above
            raise
        print(f"Unexpected error during content generation: {str(e)}")
        raise Exception(f"Failed to generate content: {str(e)}")

def save_material_to_db(subject, topic, content, user_id):
    """Save generated material to database"""
    print(f"Attempting to save generated material to database")
    
    try:
        # Validate database connection
        if not db:
            print("Warning: Database not initialized, cannot save material")
            return None
        
        # Safely process topic for filename creation
        safe_topic = "".join(c if c.isalnum() or c in '_-' else '_' for c in topic)
        if not safe_topic:
            safe_topic = "untitled"
        
        # Find corresponding subject_id (with error handling)
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
            "subject_id": subject_id,
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
        return jsonify({"error": str(e)}), 500
