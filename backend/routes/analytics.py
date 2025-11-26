from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from bson.objectid import ObjectId
import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

db = None

def init_db(db_instance):
    """Initializes the database connection for the analytics blueprint."""
    global db
    db = db_instance

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# --- LLM Utility Function (Self-Contained for Report Generation using DeepSeek API) ---
def _generate_llm_report_content(prompt, model="deepseek-chat"):
    """Makes a request to the DeepSeek API for content generation (OpenAI compatible format)."""
    
    # --- DEEPSEEK CONFIGURATION ---
    # NOTE: You must set the DEEPSEEK_API_KEY environment variable for this to work.
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") 
    # Use the standard OpenAI-compatible completions endpoint
    API_URL = "https://api.deepseek.com/v1/chat/completions" 
    
    if not DEEPSEEK_API_KEY:
        return "Error: DEEPSEEK_API_KEY environment variable not set."

    system_prompt = "You are a helpful and positive educational assistant. Your task is to generate a concise, encouraging, and actionable student performance report based on the data provided. Respond ONLY with the report text."

    # DeepSeek/OpenAI API Payload Structure
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "stream": False
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
    }

    # Simple exponential backoff retry mechanism
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.post(API_URL, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status() 
        result = response.json()
        
        # Extract the generated text from the standard completions response
        text = result.get('choices', [{}])[0].get('message', {}).get('content')
        return text if text else "LLM generated an empty response."

    except requests.exceptions.RequestException as e:
        print(f"DeepSeek API Error: {e}")
        # Log the full error response for debugging, if available
        try:
            error_details = response.json().get('error', {}).get('message', 'No message provided.')
        except:
            error_details = "Check your API key and base URL."
            
        return f"Error communicating with AI service: {e}. Details: {error_details}"


# In analytics.py

from datetime import datetime # Add this import at the top

def serialise_doc(doc):
    """Converts a MongoDB document to a serializable dictionary."""
    if not doc:
        return None
        
    # 1. Handle ObjectId -> String
    if isinstance(doc.get('_id'), ObjectId):
        doc['id'] = str(doc.pop('_id'))
    else:
        # If _id is already a string (e.g., "S001"), just rename it to id
        doc['id'] = str(doc.pop('_id'))
        
    # 2. Handle Date Objects (Crucial for MongoDB dates)
    # This prevents "Object of type datetime is not JSON serializable" errors
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat() # Convert date to string (ISO 8601)

    return doc

# Endpoint to fetch student analytics data (list view)
@analytics_bp.route('/students', methods=['GET'])
@jwt_required()
def get_student_analytics():
    if db is None:
        return jsonify({"error": "Database not initialized"}), 500

    try:
        # Attempt to fetch real data
        students = list(db.students.find({}))
        
        if not students:
            print("INFO: 'students' collection is empty. Using mock data.")

        # Serialize documents for JSON response
        results = [serialise_doc(s.copy()) for s in students]
        return jsonify(results), 200

    except Exception as e:
        print(f"Error fetching student analytics: {e}")
        return jsonify({"error": str(e)}), 500


# Endpoint to generate the AI report for a specific student
@analytics_bp.route('/report', methods=['POST'])
@jwt_required()
def generate_ai_report():
    if db is None:
        return jsonify({"error": "Database not initialized"}), 500

    data = request.get_json()
    student_id = data.get('student_id')

    if not student_id:
        return jsonify({"error": "Student ID is required."}), 400

    student_data = None
    
    try:
        # 1. Try to find student in the Database first
        mongo_id = None
        
        # If it looks like a valid Mongo ObjectId, try converting it
        if ObjectId.is_valid(student_id):
            mongo_id = ObjectId(student_id)
            student_data = db.students.find_one({"_id": mongo_id})
        
        # If not found by ObjectId, try searching as a string (e.g., "S001")
        if not student_data:
            student_data = db.students.find_one({"_id": student_id})

        # 2. Only check mock data if REAL data wasn't found
        if not student_data:
            print(f"Student {student_id} not found in DB.")

    # ... rest of the function ...

        # 3. Prepare data for the LLM
        summary_data = {
            "name": student_data.get('name', 'N/A'),
            "progress": student_data.get('progress', 0),
            "avgQuizScore": student_data.get('avgQuizScore', 0),
            "aiInteractions": student_data.get('aiInteractions', 0),
            "lastActivity": student_data.get('lastActivity', 'N/A'),
        }

        # 4. Construct the detailed prompt
        prompt = (
            f"Generate a concise, encouraging, and actionable performance report for the student: {summary_data['name']}."
            f"The report should analyze their performance based on the following key metrics and provide one actionable recommendation for improvement. "
            f"Metrics: Progress={summary_data['progress']}%, Average Quiz Score={summary_data['avgQuizScore']}%, AI Interaction Count={summary_data['aiInteractions']}."
            f"Write the report in a single, professional paragraph."
        )
        
        # 5. Call the local, simple LLM function
        report_text = _generate_llm_report_content(prompt)

        # 6. Check for LLM errors (like API key missing or internal error)
        if report_text and not report_text.startswith("Error:"):
            return jsonify({"report": report_text}), 200
        else:
            return jsonify({"error": f"LLM failed to generate content: {report_text}"}), 500

    except Exception as e:
        print(f"Error in AI report generation: {e}")
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500