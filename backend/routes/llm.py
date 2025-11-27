from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from datetime import datetime
import base64
import hashlib
import hmac
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

# Global configuration variables initialized in on_load
XF_PPT_APP_ID = None
XF_PPT_SECRET = None
XF_PPT_BASE_URL = "https://zwapi.xfyun.cn"

@llm_bp.record_once
def on_load(state):
    """Loads configuration variables from Flask app config."""
    global XF_PPT_APP_ID, XF_PPT_SECRET, XF_PPT_BASE_URL
    
    app = state.app
    
    # XF PPT Configuration
    XF_PPT_APP_ID = app.config.get("XF_PPT_APP_ID")
    XF_PPT_SECRET = app.config.get("XF_PPT_SECRET")
    XF_PPT_BASE_URL = app.config.get("XF_PPT_BASE_URL", XF_PPT_BASE_URL)
    
    print(f"XF PPT AppId loaded: {'YES' if XF_PPT_APP_ID else 'NO XF_PPT_APP_ID'}")
    print(f"XF PPT Base URL: {XF_PPT_BASE_URL}")

# --- Utility Functions ---

def get_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 429), # Add 429 for rate limiting
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

def xf_ppt_headers() -> dict:
    """
    Construct PPTv2 authentication header (appId, timestamp, signature).
    """
    if not XF_PPT_APP_ID or not XF_PPT_SECRET:
        raise Exception("XF PPTv2 is not configured (XF_PPT_APP_ID / XF_PPT_SECRET missing)")

    ts = int(time.time())  
    # Use f-string formatting for MD5 input
    md5_text = hashlib.md5(f"{XF_PPT_APP_ID}{ts}".encode("utf-8")).hexdigest()
    raw_hmac = hmac.new(
        XF_PPT_SECRET.encode("utf-8"),
        md5_text.encode("utf-8"),
        hashlib.sha1
    ).digest()
    signature = base64.b64encode(raw_hmac).decode("utf-8")

    print(f"[Auth Debug] appId={XF_PPT_APP_ID}, ts={ts}, md5={md5_text}, sig={signature[:20]}...")

    return {
        "appId": XF_PPT_APP_ID,
        "timestamp": str(ts),
        "signature": signature,
    }

def xf_post_multipart(path: str, data: dict | None = None, files: dict | None = None) -> dict:
    """Call zwapi.xfyun.cn multipart/form-data interface."""
    if data is None:
        data = {}

    # Use utility function for session
    session = get_session() 
    headers = xf_ppt_headers() 
    url = f"{XF_PPT_BASE_URL}{path}"

    if files:
        # If files present, let requests auto-set multipart
        headers.pop('Content-Type', None)  # Remove if exists, let requests set it
    else:
        # For form-urlencoded data
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    print(f"POST {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")

    resp = session.post(url, data=data, files=files, headers=headers, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    # Simple logging for debugging and rate limiting
    if result.get("code") != 0:
        print(f"XF PPT create API failed/warning: {result}")
        if result.get("code") == 402:
            # Re-raise with specific message for custom handling
            raise requests.exceptions.HTTPError("402 XF balance insufficient! Please recharge $1 USD!")

    return result

def xf_get(path: str, params: dict) -> dict:
    """Call zwapi.xfyun.cn GET interface."""
    # Use utility function for session
    session = get_session() 
    headers = xf_ppt_headers()
    url = f"{XF_PPT_BASE_URL}{path}"

    resp = session.get(url, params=params, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

# --- PPT Endpoints (XF PPT) ---

@llm_bp.route('/ppt/create', methods=['POST'])
@jwt_required()
def ppt_create():
    """Interface for generating PPT via XF API."""
    try:
        current_user_id = get_jwt_identity()
        print(f"PPT create request from user: {current_user_id}")

        data = request.form.to_dict() or request.get_json(silent=True) or {}

        # Get and sanitize parameters
        subject = (data.get("subject") or "").strip()
        topic = (data.get("topic") or "").strip()
        instruction = (data.get("instruction") or data.get("description") or "").strip()
        template_id = (data.get("templateId") or "").strip()
        # Default author to 'SmartDoc', language to 'en'
        author = (data.get("username") or "").strip() or "SmartDoc" 
        language = (data.get("language") or "en").strip()      # Default to English
        # Store subject_id for uploading files to db/material-add
        subject_id = (data.get('subject_id') or "")

        # Construct 'query' for the XF API (prefer explicit query or combine parts)
        query = (data.get("query") or "").strip()
        if not query:
            query_parts = []
            if subject:
                query_parts.append(f"Subject: {subject}")
            if topic:
                query_parts.append(f"Topic: {topic}")
            if instruction:
                query_parts.append(f"Additional instructions: {instruction}")
            
            if not query_parts:
                 return jsonify({"error": "Subject and topic are required or a direct query must be provided"}), 400
                 
            query = ". ".join(query_parts)  
        form = {
            "query": query,
            "language": language,
            "author": author,
        }
        if template_id:
            form["templateId"] = template_id

        print(f"Calling XF PPT create with query: {query}")

        try:
            result = xf_post_multipart("/api/ppt/v2/create", data=form)
        except requests.exceptions.HTTPError as e:
            if "402" in str(e):
                # Use a consistent error message format
                return jsonify({"error": "XF balance insufficient! Please recharge $1 USD!"}), 402
            raise e # Re-raise other errors
        
        # Save PPT task regardless of XF's 'flag' or specific codes, as long as sid exists
        if result.get("data", {}).get("sid"):
            save_ppt_task(current_user_id, result["data"]["sid"], subject, topic, instruction, template_id, author, language, subject_id)
        
        return jsonify(result), 200

    except Exception as e:
        print(f"Error creating PPT: {e}")
        # Catch and handle the 402 error specifically if it wasn't caught in xf_post_multipart
        if "402" in str(e):
            return jsonify({"error": "XF 餘額不足！充值 $1 USD！"}), 402
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@llm_bp.route('/ppt/progress', methods=['GET'])
@jwt_required()
def ppt_progress():
    """Interface for querying PPT generation progress & retrieving pptUrl."""
    sid = (request.args.get("sid") or "").strip()
    if not sid:
        return jsonify({"error": "sid is required"}), 400

    current_user_id = get_jwt_identity()

    try:
        result = xf_get("/api/ppt/v2/progress", params={"sid": sid})
        print(f"PPT progress result for sid {sid}: {result}")
        # Process and save the file only if generation is done and URL is present
        data = result.get("data", {})
        print(f"Processing PPT progress data: {data}")
        if data.get("pptStatus") == "done" and data.get("pptUrl"):
            ppt_url = data["pptUrl"]
            print(f"PPT generation done, URL: {ppt_url}")
            
            # Query PPT task information
            ppt_task = db.ppt_tasks.find_one({"sid": sid, "created_by": current_user_id})
            if ppt_task:
                subject = ppt_task.get("subject", "Unknown")
                topic = ppt_task.get("topic", "Unknown")
                
                # Generate safe filename
                safe_topic = "".join(c if c.isalnum() or c in '_-' else '_' for c in topic)
                safe_topic = safe_topic[:50] if safe_topic else "untitled"
                filename = f"{safe_topic}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pptx"
                
                print(f"PPT generation completed, attempting to save file: {filename}")
                
                subject_id = ppt_task.get("subject_id")

                # Save to GridFS and materials collection
                material = save_ppt_file_to_db(current_user_id, subject, topic, ppt_url, filename, subject_id)
                
                if material:
                    # Only update the task if the material was successfully saved
                    db.ppt_tasks.update_one(
                        {"_id": ppt_task["_id"]},
                        {"$set": {"status": "done", "saved_material_id": material.get("material_id")}}
                    )
                    # Return the material json in the response for frontend use
                    result["data"]["material"] = material
        return jsonify(result), 200

    except Exception as e:
        print(f"Error querying PPT progress: {e}")
        return jsonify({"error": f"Error querying PPT progress: {str(e)}"}), 500
 

def save_ppt_task(user_id: str, sid: str, subject: str, topic: str, instruction: str, template_id: str, author: str, language: str, subject_id: str):
    """Save PPT task information to database"""
    print(f"Attempting to save PPT task to database: {sid}")
    
    try:
        if db is None:
            print("Warning: Database not initialized, cannot save PPT task")
            return None
        
        ppt_task_doc = {
            "sid": sid,
            "subject": subject,
            "subject_id": subject_id,
            "topic": topic,
            "instruction": instruction,
            "template_id": template_id,
            "author": author,
            "language": language,
            "created_by": user_id,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        result = db.ppt_tasks.insert_one(ppt_task_doc)
        return result.inserted_id
        
    except Exception as e:
        print(f"Error saving PPT task to database: {str(e)}")
        return None


def save_ppt_file_to_db(user_id: str, subject: str, topic: str, ppt_url: str, filename: str, subject_id: str):
    """Download and save PPT file to MongoDB GridFS and create record only in materials collection"""
    print(f"Attempting to download and save PPT file from: {ppt_url}")
    
    # Set up URL and headers for internal POST to /db/material-add
    
    if not subject_id:
        # Find corresponding subject_id
        try:
            subject_doc = db.subjects.find_one({"subject": subject})
            if subject_doc and "_id" in subject_doc:
                subject_id = subject_doc["_id"]
        except Exception as db_err:
            print(f"Warning: Error finding subject in database: {str(db_err)}")
    try:
        base = request.host_url.rstrip('/')
        auth_hdr = {}
        auth = request.headers.get("Authorization")
        if auth:
            auth_hdr["Authorization"] = auth
        
        session = get_session()
        url = f"{base}/db/material-add"

        print(f"Preparing to post material via /db/material-add route at {url}")
        print(f"Subject ID: {subject_id}, Topic: {topic}, User ID: {user_id}")
    except Exception as e:
        raise Exception(f"Error preparing url: {str(e)}")

    try:
        
        # Download PPT file
        response = session.get(ppt_url, stream=True, timeout=300)
        response.raise_for_status() # Check for bad status codes        
      
        # Make the POST request through /db/material-add
        try:
            # Prepare file object
            files = {
                "file": (filename, response.content, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            }

            data = {
                "subject_id": str(subject_id) if subject_id else "",
                "topic": topic,
                "user_id": user_id,
                "create_type": "generate"
            }

            resp = session.post(
                url,
                files=files,
                data=data,
                headers=auth_hdr,
                timeout=30
            )
            resp.raise_for_status()
            material_result = resp.json()

            print(f"Material successfully posted via /db/material-add: {material_result}")

            return material_result
        except Exception as e:
            raise Exception(f"Failed to save material via /db/material-add route: {str(e)}")
        
    except Exception as e:
        print(f"Error saving PPT file to database: {str(e)}")
        return None  

# === Test Endpoint ===

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

# test endpoint for XF authentication
@llm_bp.route('/test/xf-auth', methods=['POST'])
@jwt_required()
def test_xf_auth():
    """Test endpoint to verify XF API authentication without creating PPT"""
    try:
        print("=== Testing XF API Authentication ===")
        
        # Call xf_post_multipart with minimal test data
        test_data = {
            "query": "Test query",
            "language": "en",
            "author": "TestUser"
        }
        
        print(f"Calling xf_post_multipart with: {test_data}")
        result = xf_post_multipart("/api/ppt/v2/create", data=test_data)
        
        print(f"✅ Success! XF API response: {result}")
        return jsonify({
            "status": "success",
            "message": "XF API authentication is working",
            "response": result
        }), 200
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        return jsonify({
            "status": "error",
            "message": f"HTTP Error: {str(e)}",
            "error_code": 405 if "405" in str(e) else "unknown"
        }), 500
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
import time
from threading import Thread

# Test storage for simulated PPT tasks
TEST_PPT_TASKS = {}

@llm_bp.route('/test/ppt/create', methods=['POST'])
@jwt_required()
def test_ppt_create():
    """Test endpoint for PPT creation with simulated delay"""
    try:
        current_user_id = get_jwt_identity()
        print(f"TEST PPT create request from user: {current_user_id}")

        data = request.form.to_dict() or request.get_json(silent=True) or {}

        # Get and sanitize parameters
        subject = (data.get("subject") or "Test Subject").strip()
        topic = (data.get("topic") or "Test Topic").strip()
        instruction = (data.get("instruction") or "").strip()
        username = (data.get("username") or "TestUser").strip()
        subject_id = (data.get("subject_id") or "507f1f77bcf86cd799439011").strip()

        # Generate test SID
        test_sid = f"test_sid_{current_user_id}_{int(time.time())}"
        
        print(f"Creating test PPT task: {test_sid}")
        print(f"Subject: {subject}, Topic: {topic}")

        # Save test PPT task
        TEST_PPT_TASKS[test_sid] = {
            "sid": test_sid,
            "subject": subject,
            "topic": topic,
            "instruction": instruction,
            "username": username,
            "subject_id": subject_id,
            "created_by": current_user_id,
            "created_at": datetime.utcnow(),
            "status": "processing",
            "progress": 0,
            "start_time": time.time()
        }

        # Simulate async processing (in real scenario, this would be async)
        def simulate_generation():
            """Simulate PPT generation with progress updates"""
            print(f"Starting simulated generation for {test_sid}")
            
            # Simulate 20 seconds of generation
            for i in range(20):
                time.sleep(1)
                progress = (i + 1) * 5
                TEST_PPT_TASKS[test_sid]["progress"] = progress
                print(f"[{test_sid}] Progress: {progress}%")
            
            # After "generation", set status to done and add mock URL
            TEST_PPT_TASKS[test_sid]["status"] = "done"
            TEST_PPT_TASKS[test_sid]["progress"] = 100
            TEST_PPT_TASKS[test_sid]["pptUrl"] = f"https://example.com/ppt/{test_sid}.pptx"
            print(f"[{test_sid}] Generation complete!")

        # Start simulation in background thread
        thread = Thread(target=simulate_generation, daemon=True)
        thread.start()

        return jsonify({
            "code": 0,
            "message": "success",
            "data": {
                "sid": test_sid,
                "message": "PPT generation started (simulated with 20 second delay)"
            }
        }), 200

    except Exception as e:
        print(f"Error in test PPT create: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500


@llm_bp.route('/test/ppt/progress', methods=['GET'])
@jwt_required()
def test_ppt_progress():
    """Test endpoint for checking PPT progress with simulated generation"""
    try:
        sid = (request.args.get("sid") or "").strip()
        if not sid:
            return jsonify({"error": "sid is required"}), 400

        current_user_id = get_jwt_identity()

        # Check if SID exists in test tasks
        if sid not in TEST_PPT_TASKS:
            return jsonify({"error": f"Test SID not found: {sid}"}), 404

        task = TEST_PPT_TASKS[sid]
        status = task.get("status", "processing")
        progress = task.get("progress", 0)

        print(f"Checking progress for {sid}: status={status}, progress={progress}%")

        # Build response
        response_data = {
            "sid": sid,
            "pptStatus": status,
            "progress": progress
        }

        # If done, add mock material data and retrieve URL
        if status == "done":
            ppt_url = task.get("pptUrl")
            
            if ppt_url:
                print(f"PPT generation done, URL: {ppt_url}")
                
                # Query PPT task information from database
                subject = task.get("subject", "Unknown")
                topic = task.get("topic", "Unknown")
                
                # Generate safe filename
                safe_topic = "".join(c if c.isalnum() or c in '_-' else '_' for c in topic)
                safe_topic = safe_topic[:50] if safe_topic else "untitled"
                filename = f"{safe_topic}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pptx"
                
                print(f"PPT generation completed, attempting to save file: {filename}")
                
                subject_id = task.get("subject_id")
                
                # Save to GridFS and materials collection
                material = save_ppt_file_to_db(current_user_id, subject, topic, ppt_url, filename, subject_id)
                
                if material:
                    response_data["pptUrl"] = ppt_url
                    response_data["material"] = material
            else:
                # Fallback to mock material if no URL retrieved
                mock_material = {
                    "material_id": f"material_{sid}",
                    "subject": task.get("subject"),
                    "topic": task.get("topic"),
                    "filename": f"{task.get('topic')}_generated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pptx",
                    "uploaded_by": current_user_id,
                    "created_at": task.get("created_at").isoformat(),
                    "file_size": 2048576,
                    "file_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                }
                response_data["material"] = mock_material

        return jsonify({
            "code": 0,
            "message": "success",
            "data": response_data
        }), 200

    except Exception as e:
        print(f"Error in test PPT progress: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500


@llm_bp.route('/test/ppt/reset', methods=['POST'])
@jwt_required()
def test_ppt_reset():
    """Reset all test PPT tasks (useful for testing)"""
    try:
        count = len(TEST_PPT_TASKS)
        TEST_PPT_TASKS.clear()
        return jsonify({
            "message": f"Cleared {count} test PPT tasks"
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@llm_bp.route('/test/ppt/download', methods=['GET'])
@jwt_required()
def test_ppt_download():
    """Test endpoint to download PPT using real XF API flow"""
    try:
        sid = (request.args.get("sid") or "").strip()
        if not sid:
            return jsonify({"error": "sid is required"}), 400

        current_user_id = get_jwt_identity()
        print(f"Testing PPT download for sid: {sid}")

        # Step 1: Call xf_get to check progress and get pptUrl
        print(f"Step 1: Calling xf_get to retrieve pptUrl...")
        result = xf_get("/api/ppt/v2/progress", params={"sid": sid})
        print(f"XF progress result: {result}")

        data = result.get("data", {})
        ppt_url = data.get("pptUrl")
        status = data.get("pptStatus")

        if not ppt_url:
            return jsonify({
                "error": "PPT URL not available",
                "status": status,
                "message": "PPT generation may still be in progress"
            }), 400

        print(f"Step 2: Retrieved pptUrl: {ppt_url}")

        # Step 3: Download the PPT file from the retrieved URL
        print(f"Step 3: Downloading PPT file from URL...")
        session = get_session()
        response = session.get(ppt_url, stream=True, timeout=300)
        response.raise_for_status()

        file_size = len(response.content)
        print(f"Step 4: Successfully downloaded {file_size} bytes")

        # Return download response
        return Response(
            response.content,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename=test_ppt_{sid}.pptx"}
        )

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error during download: {e}")
        return jsonify({"error": f"HTTP Error: {str(e)}"}), 500
    except Exception as e:
        print(f"Error in test PPT download: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error: {str(e)}"}), 500
    
@llm_bp.route('/test/ppt/check-url', methods=['GET'])
@jwt_required()
def test_ppt_check_url():
    """Debug endpoint to check pptUrl from XF API for a given SID"""
    try:
        sid = (request.args.get("sid") or "").strip()
        if not sid:
            return jsonify({"error": "sid is required"}), 400

        current_user_id = get_jwt_identity()
        print(f"Checking pptUrl for sid: {sid}")

        # Call xf_get to retrieve progress
        result = xf_get("/api/ppt/v2/progress", params={"sid": sid})
        print(f"Full XF API response: {result}")

        # Extract all fields
        data = result.get("data", {})
        
        return jsonify({
            "full_response": result,
            "data_object": data,
            "pptStatus": data.get("pptStatus"),
            "pptUrl": data.get("pptUrl"),
            "has_url": bool(data.get("pptUrl")),
            "url_type": type(data.get("pptUrl")).__name__ if data.get("pptUrl") else "None",
            "debug_info": {
                "sid": sid,
                "response_code": result.get("code"),
                "response_desc": result.get("desc"),
                "response_flag": result.get("flag")
            }
        }), 200

    except Exception as e:
        print(f"Error in test_ppt_check_url: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500