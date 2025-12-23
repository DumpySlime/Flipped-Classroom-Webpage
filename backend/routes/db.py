from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
import os
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
db = None
fs = None
SIGNER = None
PUBLIC_BASE_URL = None

db_bp = Blueprint('db', __name__)

@db_bp.record_once
def register_signer(setup_state):
    global SIGNER, PUBLIC_BASE_URL
    app = setup_state.app
    SIGNER = URLSafeTimedSerializer(
        app.config["OFFICE_SECRET_KEY"],
        salt="pptx-embed"
    )
    PUBLIC_BASE_URL = app.config["PUBLIC_BASE_URL"]

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

# Material CRUD operations
# Add Material
# create a temporary object in db once press generate first, add a 'progress' field to track status
@db_bp.route('/material-add', methods=['POST'])
@jwt_required()
def add_material():
    try:
        if "file" not in request.files:
            return {"error": "No file part in the request"}, 400
        f = request.files.get('file')
        subject_id = request.form.get('subject_id')
        topic = request.form.get('topic')

        create_type = request.form.get('create_type', 'undefined')  # 'upload' or 'generate'

        try:
            user_id = ObjectId(request.form.get('user_id'))
        except Exception as e:
            print("No user_id in form, getting from token")
            user_id = getUserById(get_jwt_identity())['_id']  
        if not f:
            return {"error": "file is required"}, 400
        if not subject_id:
            return {"error": "subject_id is required"}, 400
        if not topic:
            return {"error": "topic is required"}, 400

        metadata = {
            'subject_id': ObjectId(subject_id),
            'topic': topic,
            'uploaded_by': user_id,
            'upload_date': datetime.now(),
            'filename': f.filename
        }

        file_id = fs.put(
            f.stream, 
            filename=f.filename,
            content_type=f.mimetype, 
            metadata=metadata)
        
        gf = fs.get(file_id)

        mat = {
            'file_id': ObjectId(file_id),
            'filename': gf.filename,
            'subject_id': ObjectId(subject_id),
            'topic': topic,
            'uploaded_by': user_id,
            'create_type': create_type,
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
                "subject_id": subject_id,
                "topic": topic,
                "uploaded_by": str(user_id),
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
        subject_id = request.args.get('subject_id')
        topic = request.args.get('topic')
        uploaded_by = request.args.get('uploaded_by')

        print(f'Query params: material_id={material_id}, filename={filename}, subject_id={subject_id}, topic={topic}, uploaded_by={uploaded_by}')
        
        filt = {}
        if material_id:
            filt['_id'] = ObjectId(material_id)
        if filename:
            filt['filename'] = filename
        if subject_id:
            filt['subject_id'] = ObjectId(subject_id)
        if topic:
            filt['topic'] = topic
        if uploaded_by:
            filt['uploaded_by'] = ObjectId(uploaded_by)

        print(f'MongoDB filter: {filt}')

        mats = list(db.materials.find(filt, {}))

        print(f'Found {len(mats)} materials')

        if not mats and not filt:
            all_mats = list(db.materials.find({}).limit(5))
            print(f'Sample materials in DB: {all_mats}')

        materials = []
        for m in mats:
            materials.append({
                "id": str(m["_id"]),
                "file_id": str(m["file_id"]),
                "filename": m.get("filename"),
                "subject_id": str(m.get("subject_id")),
                "topic": m.get("topic"),
                "uploaded_by": str(m.get("uploaded_by")),
                "upload_date": m.get("upload_date").strftime("%Y/%m/%d") if m.get("upload_date") else None,
                "content_type": m.get("content_type")
            })
        print(f'Materials of {subject_id}:', materials)
        if not materials:
            return jsonify({"message": "No materials found"}), 404
        return jsonify({"materials": materials}), 200
    except Exception as e:
        return {"error": str(e)}, 500

# Delete Material
@db_bp.route('/material-delete', methods=['DELETE'])
@jwt_required()
def delete_material():
    print("Received request to delete material")
    try:
        material_id = request.args.get('material_id')
        print(f"Received request to delete material with id: {material_id}")
        if not material_id:
            print("material_id is missing in request")
            return {"error": "material_id is required"}, 400
        mat = db.materials.find_one({'_id': ObjectId(material_id)})
        if not mat:
            print(f"Material with id {material_id} not found")
            return {"error": "Material not found"}, 404
        print(f"Deleting file with id {mat['file_id']}")
        fs.delete(mat['file_id'])
        db.materials.delete_one({'_id': ObjectId(material_id)})
        return jsonify({"message": "Material deleted successfully"}), 200
    except Exception as e:
        return {"error": str(e)}, 500
    
# process ppt
# create a short-lived signed URL
@db_bp.route('/material/<file_id>/signed-url', methods=['GET'])
@jwt_required()
def get_signed_url(file_id):
    user_id = get_jwt_identity()

    # authorize file
    mat = db.materials.find_one({'file_id': ObjectId(file_id)}, {'_id': 1, 'subject_id': 1, 'uploaded_by': 1})
    if not mat:
        return jsonify({'error': 'Forbidden'}), 403

    token = SIGNER.dumps({"f_id": file_id, "u_id": str(user_id)})
    
    base_url = os.environ.get('PUBLIC_BASE_URL', request.host_url.rstrip('/'))
    public_url = base_url + f"/db/public/pptx/{token}"
    
    print(f"Generated signed URL: {public_url}")

    return jsonify({"url": public_url}), 200


# public route for office web viewer
@db_bp.route("/public/pptx/<token>", methods=['GET'])
def display_pptx(token):
    try:
        data = SIGNER.loads(token, max_age=600) # 10 minutes of access
    except SignatureExpired:
        return jsonify({"error": "Powerpoint link expired"}), 410
    except BadSignature:
        return jsonify({"error": "Invalid link"}), 400
    
    fid = data.get("f_id")
    try: 
        file = fs.get(ObjectId(fid))
    except Exception:
        return jsonify({"error": "File not found"}), 404

# stream in chunks so large files don’t load into memory
    def generate():
        chunk = file.read(8192)
        while chunk:
            yield chunk
            chunk = file.read(8192)

    headers = {
        "Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "Content-Disposition": f'inline; filename="{file.filename or "slide.pptx"}"',
        "Cache-Control": "no-store",  # viewer can fetch within token lifetime; tune as needed
    }
    return Response(generate(), headers=headers)

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
                "id": u["_id"],
                "username": u.get("username")
            })
        print("User search results:", results)
        return jsonify({"users": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Subject CRUD operations
# Add Subject
@db_bp.route("/subject-add", methods=['POST'])
@jwt_required()
def add_subject():
    try:
        data = request.get_json()

        subject = (data.get("subject") or "").strip()
        topics = data.get("topics") or []
        teacher_ids = data.get("teacher_ids") or []  
        student_ids = data.get("student_ids") or []
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
                print("added teacher id: ", tid)
            except Exception:
                return jsonify({"error": f"error: {tid}"}), 400
            
        if valid_teacher_ids:
            count = db.users.count_documents({"_id": {"$in": valid_teacher_ids}, "role": "teacher"})
            print("Validating teacher IDs, found count:", count)
            print("Valid teacher IDs:", valid_teacher_ids)
            if count != len(valid_teacher_ids):
                return jsonify({"error": "one or more teacher ids are invalid or not teachers"}), 400

        print("Received student IDs for subject creation:", student_ids)
        valid_student_ids = []
        for sid in student_ids:
            try:
                valid_student_ids.append(ObjectId(sid))
            except Exception:
                return jsonify({"error": f"invalid student id: {sid}"}), 400
            
        if valid_student_ids:
            count = db.users.count_documents({"_id": {"$in": valid_student_ids}, "role": "student"})
            print("Validating student IDs, found count:", count)
            print("Valid student IDs:", valid_student_ids)
            if count != len(valid_student_ids):
                return jsonify({"error": "one or more student ids are invalid or not student"}), 400

                
        existing = db.subjects.find_one({"subject": subject})
        if existing:
            return jsonify({"error": "subject already exists"}), 409
        doc = {
            "subject": subject,
            "topics": clean_topics,
            "teacher_ids": valid_teacher_ids,
            "student_ids": valid_student_ids,
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
@db_bp.route('/subject', methods=['GET'])
@jwt_required()
def get_subject():
    try:
        id = request.args.get('id')
        subject = request.args.get('subject')
        teacher_id = request.args.get('teacher_id')
        student_id = request.args.get('student_id')
        filt = {}
        if (id):
            filt['_id'] = ObjectId(id)
        if (subject):
            filt['subject'] = subject
        if (teacher_id):
            filt['teacher_ids'] = ObjectId(teacher_id)
        if (student_id):
            filt['student_ids'] = ObjectId(student_id)
        subjects = list(db.subjects.find(filt))
        results = []
        for u in subjects:
            results.append({
                "id": str(u["_id"]),
                "subject": u.get("subject"),
                "topics": u.get("topics"),
                "teacher_ids": [str(tid) for tid in u.get("teacher_ids", [])],
                "student_ids": [str(tid) for tid in u.get("student_ids", [])],
                "created_by": str(u["created_by"]),
                "created_at": u.get("created_at").isoformat(),
                "updated_at": u.get("updated_at").isoformat()
            })
        print("Subject search results:", results)
        return jsonify({"subjects": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Question CRUD operations
# Add Question
@db_bp.route('/question-add', methods=['POST'])
@jwt_required()
def add_question():
    try:
        data = request.get_json()
        created_by = data.get("user_id")
        question_content = data.get("question_content") or None
        create_type = data.get("create_type", "undefined")  # 'upload' or 'generate'
        material_id = data.get("material_id") or "69273672bf870f9934222d4b" # default material id for questions without material
        if not question_content:
            return jsonify({"error": "question_text is required"}), 400
        doc = {
            "material_id": ObjectId(material_id),
            "question_content": question_content,
            "created_by": ObjectId(created_by),
            "create_type": create_type,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        print ("Inserting question document:", doc)
        res = db.questions.insert_one(doc)
        doc["_id"] = res.inserted_id
        doc_serializable = {**doc, "_id": str(res.inserted_id)}
        return jsonify({"questions": [doc_serializable]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Get Questions
@db_bp.route('/question', methods=['GET'])
@jwt_required()
def get_question():
    try:
        material_id = request.args.get('material_id')
        filt = {}
        if (material_id):
            filt['material_id'] = ObjectId(material_id)
        questions = list(db.questions.find(filt))
        results = []
        for u in questions:
            results.append({
                "id": str(u["_id"]),
                "subject_id": str(u.get("subject_id")),
                "material_id": str(u.get("material_id")),
                "topic": u.get("topic"),
                "question_content": u.get("question_content"),
                "created_by": str(u["created_by"]),
                "create_type": u.get("create_type"),
                "created_at": u.get("created_at").isoformat(),
                "updated_at": u.get("updated_at").isoformat()
            })
        print("Question search results:", results)
        return jsonify({"questions": results}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500