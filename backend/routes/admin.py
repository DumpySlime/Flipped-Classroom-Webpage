from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from datetime import datetime
from flask_bcrypt import Bcrypt

db = None

def init_db(db_instance):
    global db
    db = db_instance

admin_bp = Blueprint('admin', __name__)

def admin_auth():
    current_user_id = get_jwt_identity()
    current_user = db.users.find_one({"_id": ObjectId(current_user_id)})
    if not current_user or current_user.get('role', '').lower() == "admin":
        return jsonify({"error": "Admin access is required"})
    
@admin_bp.route('/users', methods=['GET'])
def get_users():
    try:
        username = request.args.get("username")
        role = request.args.get("role")
        firstName = request.args.get("firstName")
        lastName = request.args.get("lastName")
        filt = {}
        if role:
            filt["role"] = role
        if username:
            filt["username"] = username
        if username:
            filt["firstName"] = firstName
        if username:
            filt["lastName"] = lastName
        docs = list(db.users.find(filt, {"password": 0, "firstName": 0, "lastName": 0, "role": 0}))
        results = []
        for u in docs:
            results.append({
                "id": str(u["_id"]),
                "username": u.get("username")
            })
        print("User search results:", results)
        return jsonify({"users": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/user/add', methods=['POST'])
def add_user():
    data = request.get_json()
    required_fields = ["username", "password", "firstName", "lastName", "role"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400
    existing = db.users.find_one({"username": data["username"]})
    if existing:
        return jsonify({"error": "username already exists"}), 409
    # Hash password
    hashed_password = Bcrypt().generate_password_hash(data["password"]).decode('utf-8')
    user_doc = {
        "username": data["username"],
        "password": hashed_password,
        "firstName": data["firstName"],
        "lastName": data["lastName"],
        "role": data["role"]
    }
    db.users.insert_one(user_doc)
    return jsonify({"message": "User added successfully"}), 201

@admin_bp.route("/api/subject/add", methods=['POST'])
def add_subject():
    data = request.get_json()

    if not all(key in data for key in ["subject", "topics", "teachers"]):
        return jsonify({"error": "Missing required fields"}), 400

    subject = (data.get("subject") or "").strip()
    topics = data.get("topics") or []
    teacher_ids = data.get("teachers") or []  

    if not subject:
        return jsonify({"error": "subject is required"}), 400
    # clean u topic
    topics = lambda topics: [s for s in ((t or "").strip() for t in (topics or [])) if s]

    print("Received teacher IDs for subject creation:", teacher_ids)
    valid_teacher_ids = []
    for tid in teacher_ids:
        try:
            valid_teacher_ids.append(ObjectId(tid))
        except Exception:
            return jsonify({"error": f"invalid teacher id: {tid}"}), 400
        
        if valid_teacher_ids:
            count = db.user.count_documents({"_id": {"$in": valid_teacher_ids}, "role": "teacher"})
            print("Validating teacher IDs, found count:", count)
            print("Valid teacher IDs:", valid_teacher_ids)
            if count != len(valid_teacher_ids):
                return jsonify({"error": "one or more teacher ids are invalid or not teachers"}), 400
            
    existing = db.subjects.find_one({"subject": subject})
    if existing:
        return jsonify({"error": "subject already exists"}), 409
    
    doc = {
        "subject": subject,
        "topics": topics,                 # simple list of topic strings
        "teachers": valid_teacher_ids,    # array of ObjectId
        "created_by": get_jwt_identity(),        # optional
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        # You can add meta like syllabus, grade scheme, locale, etc.
    }

    res = db.subjects.insert_one(doc)

    # Return a view-friendly payload
    return jsonify({
        "id": str(res.inserted_id),
        "subject": subject,
        "topics": topics,
        "teachers": [str(t) for t in valid_teacher_ids],
        "created_by": get_jwt_identity()
    }), 201