from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
import io
from datetime import datetime

db = None
fs = None

def init_db(db_instance, fs_instance):
    global db
    db = db_instance
    global fs
    fs = fs_instance

def getUserById(user_id):
    try:
        uploader_id = ObjectId(user_id)
    except Exception as e:
        return {"error": "Invalid user identity in token"}, 400
    
    user = db.users.find_one({'_id': uploader_id})
    if not user:
        return {"error": "User not found"}, 404
    return user

db_bp = Blueprint('db', __name__)

# Material CRUD operations
# Add Material
@db_bp.route('/material-add', methods=['POST'])
@jwt_required()
def add_material():
    try:
        if "file" not in request.files:
            return {"error": "No file part in the request"}, 400
        f = request.files.get('file')
        subject = request.form.get('subject')
        topic = request.form.get('topic')

        if not f:
            return {"error": "file is required"}, 400
        if not subject:
            return {"error": "subject is required"}, 400
        if not topic:
            return {"error": "topic is required"}, 400

        user = getUserById(get_jwt_identity())

        metadata = {
            'subject': subject,
            'topic': topic,
            'uploaded_by': user,
            'upload_date': datetime(),
            'filename': f.filename
        }

        file_id = fs.put(
            f.stream, 
            filename=f.filename,
            content_type=f.mimetype, 
            metadata=metadata)
        
        gf = fs.get(file_id)

        mat = {
            'file_id': file_id,
            'filename': gf.filename,
            'subject': subject,
            'topic': topic,
            'uploaded_by': user,
            'upload_date': gf.upload_date,
            'size_bytes': gf.length,
            'content_type': gf.content_type,
        }
        mat_id = db.materials.insert_one(mat).inserted_id
        if mat_id:
            return jsonify({
                'result': 'Material uploaded successfully',
                'material_id': str(mat_id),
                "file_id": str(file_id),
                "filename": gf.filename,
                "subject": subject,
                "topic": topic,
                "uploaded_by": str(user),
                "upload_date": gf.upload_date.isoformat(),
                "size_bytes": gf.length,
                "content_type": gf.content_type
            }),201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Materials
@db_bp.route('/material', methods=['GET'])
@jwt_required()
def get_material():
    try:
        material_id = request.args.get('material_id')
        filename = request.args.get('filename')
        subject = request.args.get('subject')
        topic = request.args.get('topic')
        uploaded_by = request.args.get('uploaded_by')
        filt = {}
        if material_id:
            filt['_id'] = ObjectId(material_id)
        if filename:
            filt['filename'] = filename
        if subject:
            filt['subject'] = subject
        if topic:
            filt['topic'] = topic
        if uploaded_by:
            filt['uploaded_by'] = ObjectId(uploaded_by)

        mats = db.materials.find(filt, {
            "file_id": 1, 
            "filename": 1, 
            "subject": 1, 
            "topic": 1, 
            "uploaded_by": 1, 
            "upload_date": 1, 
            "size_bytes": 0, 
            "content_type": 1
        })

        materials = []
        for m in mats:
            materials.append({
                "id": str(m["_id"]),
                "file_id": str(m["file_id"]),
                "filename": m.get("filename"),
                "subject": m.get("subject"),
                "topic": m.get("topic"),
                "uploaded_by": str(m.get("uploaded_by")),
                "upload_date": m.get("upload_date").isoformat() if m.get("upload_date") else None,
                "content_type": m.get("content_type")
            })

        if not materials:
            return jsonify({"message": "No materials found"}), 404
        return jsonify({"materials": materials}), 200
    except Exception as e:
        return {"error": str(e)}, 500

# Delete Material
@db_bp.route('/material-delete', methods=['DELETE'])
@jwt_required()
def delete_material():
    try:
        material_id = request.args.get('material_id')
        if not material_id:
            return {"error": "material_id is required"}, 400
        mat = db.materials.find_one({'_id': ObjectId(material_id)})
        if not mat:
            return {"error": "Material not found"}, 404
        fs.delete(mat['file_id'])
        db.materials.delete_one({'_id': ObjectId(material_id)})
        return jsonify({"message": "Material deleted successfully"}), 200
    except Exception as e:
        return {"error": str(e)}, 500
    
# User CRUD operations
# Add User
@db_bp.route('/user-add', methods=['POST'])
@jwt_required()
def add_user():
    data = request.json
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
        "role": data["role"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    db.users.insert_one(user_doc)
    return jsonify({"message": "User added successfully"}), 201

# Get Users
@db_bp.route('/user', methods=['GET'])
@jwt_required()
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
        docs = list(db.users.find(filt, {}))
        results = []
        for u in docs:
            results.append({
                "id": str(u["_id"]),
                "username": u.get("username")
            })
        print("User search results:", results)
        return jsonify({"users": docs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Subject CRUD operations
# Add Subject
@db_bp.route("/subject-add", methods=['POST'])
@jwt_required()
def add_subject():
    try:
        data = request.get_json()

        #if not all(key in data for key in ["subject", "topics", "teachers"]):
        #    return jsonify({"error": "Missing required fields"}), 400

        subject = (data.get("subject") or "").strip()
        topics = data.get("topics") or []
        teacher_ids = data.get("teachers") or []  

        if not subject:
            return jsonify({"error": "subject is required"}), 400
        # clean u topic
        clean_topics = []
        for t in topics or []:
            s = (t or "").strip()
            if s:
                clean_topics.append(s)

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
        #valid_teacher_ids = [ObjectId("690dcaa34fe33f7359ac5675"), ObjectId("690dcae74fe33f7359ac5676"), ObjectId("690dcb484fe33f7359ac567a"), ObjectId("690dd17fb1ba9740d7c402cc"), ObjectId("690dcb354fe33f7359ac5679")]
        doc = {
            "subject": subject,
            "topics": clean_topics,
            "teacher_ids": valid_teacher_ids,
            "created_by": ObjectId(get_jwt_identity()),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        res = db.subjects.insert_one(doc)
        doc["_id"] = res.inserted_id
        doc_serializable = {**doc, "_id": str(res.inserted_id)}
        return jsonify({"subjects": [doc_serializable]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Subjects
@db_bp.route('/subject', methods=['POST'])
@jwt_required()
def get_subject():
    try:
        subject = request.args.get('subject')
        teacher_id = request.args.get('teacher')
        filt = {}
        if (subject):
            filt['subject'] = subject
        if (teacher_id):
            filt['teacher_id'] = teacher_id
        subjects = list(db.subject.find(filt))
        results = []
        for u in subjects:
            results.append({
                "id": str(u["_id"]),
                "subject": u.get("subject"),
                "topics": u.get("topics"),
                "teacher_ids": [str(tid) for tid in u.get("teacher_ids", [])],
                "created_by": str[u["_id"]],
                "created_at": u.get("created_at").isoformat(),
                "updated_at": u.get("updated_at").isoformat()
            })
        print("Subject search results:", results)
        return jsonify({"subjects": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500