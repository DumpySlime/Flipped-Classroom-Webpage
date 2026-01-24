from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from bson.objectid import ObjectId
from bson.errors import InvalidId
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
        #if "file" not in request.files:
        #    return {"error": "No file part in the request"}, 400
        #f = request.files.get('file')
        subject_id = request.form.get('subject_id')
        topic = request.form.get('topic')
        slides = request.form.get('slides')
        create_type = request.form.get('create_type', 'undefined')  # 'upload' or 'generate'
        status = request.form.get('status', 'generating')  # 'generating' or 'completed'

        try:
            user_id = ObjectId(request.form.get('user_id'))
        except Exception as e:
            print("No user_id in form, getting from token")
            user_id = getUserById(get_jwt_identity())['_id']  
        #if not f:
        #    return {"error": "file is required"}, 400
        if not subject_id:
            return {"error": "subject_id is required"}, 400
        if not topic:
            return {"error": "topic is required"}, 400

        #metadata = {
        #    'subject_id': ObjectId(subject_id),
        #    'topic': topic,
        #    'uploaded_by': user_id,
        #    'upload_date': datetime.now(),
        #    'filename': f.filename
        #}

        #file_id = fs.put(
        #    f.stream, 
        #    filename=f.filename,
        #    content_type=f.mimetype, 
        #    metadata=metadata)
        
        #gf = fs.get(file_id)

        mat = {
        #    'file_id': ObjectId(file_id),
        #    'filename': gf.filename,
            'subject_id': ObjectId(subject_id),
            'topic': topic,
            'slides': slides,
            'uploaded_by': user_id,
            'status': status,
            'create_type': create_type,
            'created_at': datetime.now().isoformat(),
        #    'size_bytes': gf.length,
        #    'content_type': gf.content_type,
        }
        mat_id = db.materials.insert_one(mat).inserted_id
        if mat_id:
            return jsonify({
                'result': 'Material uploaded successfully',
                'material_id': str(mat_id),
                #    "file_id": str(file_id),
                #    "filename": gf.filename,
                "subject_id": subject_id,
                "topic": topic,
                "slides": slides,
                "uploaded_by": str(user_id),
                'status': status,
                "upload_date": datetime.now().isoformat(),
                #    "size_bytes": 0,
                #    "content_type": gf.content_type
            }),201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Get Materials
@db_bp.route('/material', methods=['GET'])
@jwt_required()
def get_material():
    try:
        material_id = request.args.get('material_id')
        #filename = request.args.get('filename')
        subject_id = request.args.get('subject_id')
        topic = request.args.get('topic')
        uploaded_by = request.args.get('uploaded_by')

        print(f'Query params: material_id={material_id}, subject_id={subject_id}, topic={topic}, uploaded_by={uploaded_by}')
        
        filt = {}
        if material_id:
            filt['_id'] = ObjectId(material_id)
        #if filename:
        #    filt['filename'] = filename
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
            all_mats = list(db.materials.find({}))
            print(f'Sample materials in DB: {all_mats}')

        materials = []
        for m in mats:
            materials.append({
                "id": str(m["_id"]),
                #"file_id": str(m["file_id"]),
                #"filename": m.get("filename"),
                "subject_id": str(m.get("subject_id")),
                "topic": m.get("topic"),
                "slides": m.get("slides"),
                "uploaded_by": str(m.get("uploaded_by")),
                "created_at": m.get("created_at"),
                # "content_type": m.get("content_type")
            })
        print(f'Materials of {subject_id}:', materials)
        if not materials:
            return jsonify({"message": "No materials found"}), 404
        return jsonify({"materials": materials}), 200
    except Exception as e:
        return {"error": str(e)}, 500

# Delete Material + Question
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
        #print(f"Deleting file with id {mat['file_id']}")
        #fs.delete(mat['file_id'])
        db.materials.delete_one({'_id': ObjectId(material_id)})
        db.questions.delete_many({'material_id': ObjectId(material_id)})
        print(f"Material with id {material_id} and associated questions deleted successfully")
        return jsonify({"message": "Material deleted successfully"}), 200
    except Exception as e:
        return {"error": str(e)}, 500
    
@db_bp.route('/material-update', methods=['PUT'])
@jwt_required()
def update_material():
    try:
        material_id = request.args.get('material_id')
        if not material_id:
            return {"error": "material_id is required"}, 400

        data = request.form.to_dict() or request.get_json(silent=True) or {}
        status = data.get("status", "generating")
        slides = data.get("slides", "")

        print(f"Updating material {material_id} with status: {status}, and slides: {slides}")

        db.materials.update_one(
            {"_id": ObjectId(material_id)},
            {
                "$set": {
                    "status": status,
                    "slides": slides
                }
            }
        )

        return jsonify({"message": "Material updated successfully"}), 200
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
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
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
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
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

# Get topics by subject_id
@db_bp.route('/topic', methods=["GET"])
@jwt_required()
def get_topic():
    try:
        subject_id = request.args.get("subject_id")
        if not subject_id:
            return jsonify({"success": False, "error": "subject_id query parameter required"}), 400
        filt = {}
        filt["subject_id"] = ObjectId(subject_id)
        docs = list(db.topics.find(filt))
        
        topics = []
        for d in docs:
            topics.append({
                "_id": str(d["_id"]),
                "subject_id": str(d.get("subject_id")) if d.get("subject_id") is not None else None,
                "topic": d.get("topic")
            })
            
        return jsonify({
            "success": True,
            "subject_id": subject_id,
            "topics": topics
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)})
        
# Get subject members
@db_bp.route("/subjectmembers", methods=["GET"])
@jwt_required() 
def get_subject_members():
    user_id = get_jwt_identity()
    
    try:
        user_doc = db.users.find_one({"_id": ObjectId(user_id)}, {"role": 1})
        user_role = user_doc.get("role") if user_doc else None
    except Exception:
        user_role = None
    
    subject_id_param = request.args.get("subject_id")
    subject_ids_filter = None

    if subject_id_param:
        try:
            subject_ids_filter = [ObjectId(subject_id_param)]
        except (InvalidId, TypeError, ValueError):
            subject_ids_filter = [subject_id_param]
    elif user_role == "teacher":
        try:
            user_oid = ObjectId(user_id)
            teacher_query = {"user_id": user_oid, "role": "teacher"}
        except Exception:
            teacher_query = {"user_id": user_id, "role": "teacher"}
        
        teacher_subjects_cursor = db.subjectMembers.find(teacher_query, {"subject_ids": 1})
        subject_ids_filter = [] 
        for doc in teacher_subjects_cursor: 
            subject_ids_filter.extend(doc.get("subject_ids", []))
    else:
        # for other roles e.g.admin, then return all students
        subject_ids_filter = None    

    pipeline = []

    # if we have a subject filter list (could be empty list)
    if subject_ids_filter is not None:
        pipeline.append({"$match": {"subject_ids": {"$in": subject_ids_filter}}})

    # IMPORTANT: if caller is teacher, restrict to subjectmembers.role == "student"
    if user_role == "teacher":
        pipeline.append({"$match": {"role": "student"}})
        
    # lookup user info
    pipeline.append({
        "$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "user"
        }
    })
    pipeline.append({"$unwind": {"path": "$user", "preserveNullAndEmptyArrays": True}})

    # lookup subjects (array join)
    pipeline.append({
        "$lookup": {
            "from": "subjects",
            "localField": "subject_ids",
            "foreignField": "_id",
            "as": "subjects"
        }
    })
    
    # project fields; role here is the subjectMembers.role (for teacher it will be 'student'),
    # you can also include account-level role if you want: "accountRole": "$user.role"
    pipeline.append({
        "$project": {
            "_id": 1,
            "subject_ids": 1,
            "subjects": "$subjects.subject",
            "user_id": 1,
            "firstName": "$user.firstName",
            "lastName": "$user.lastName",
            "role": "$role"
        }
    })

    try:
        docs = list(db.subjectMembers.aggregate(pipeline))
    except Exception as e:
        return jsonify({"success": False, "error": "database error", "details": str(e)}), 500
    
    result = []
    for d in docs:
        result.append({
            "_id": str(d.get("_id")),
            "subject_ids": [str(sid) for sid in d.get("subject_ids", [])],
            "subjects": d.get("subjects", []),
            "user_id": str(d.get("user_id")),
            "firstName": d.get("firstName"),
            "lastName": d.get("lastName"),
            "role": d.get("role")
        })
    return jsonify({"success": True, "subjectmembers": result}), 200           

# Add Question
@db_bp.route('/question-add', methods=['POST'])
@jwt_required()
def add_question():
    try:
        data = request.get_json()
        created_by = data.get("user_id")
        question_content = data.get("question_content") or None
        create_type = data.get("create_type", "undefined")
        material_id = data.get("material_id")

        if not question_content:
            return jsonify({"error": "question_content is required"}), 400

        # Handle material_id - can be ObjectId or string
        material_id_value = None
        if material_id:
            try:
                # Check if it's a valid ObjectId format
                if len(material_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in material_id):
                    material_id_value = ObjectId(material_id)
                else:
                    # For AI-generated materials with string IDs
                    material_id_value = material_id
            except:
                material_id_value = material_id

        doc = {
            "material_id": material_id_value,
            "question_content": question_content,
            "created_by": ObjectId(created_by),
            "create_type": create_type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        print("Inserting question document:", doc)
        res = db.questions.insert_one(doc)
        
        return jsonify({
            "_id": str(res.inserted_id),
            "message": "Question added successfully"
        }), 201

    except Exception as e:
        print(f"Error in add_question: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Get Questions
@db_bp.route('/question', methods=['GET'])
@jwt_required()
def get_question():
    try:
        material_id = request.args.get('material_id')
        filt = {}
        
        if material_id:
            # Try to convert to ObjectId first, if it fails, use string
            try:
                # Check if it's a valid ObjectId format (24 hex chars)
                if len(material_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in material_id):
                    filt['material_id'] = ObjectId(material_id)
                else:
                    # For AI-generated materials with string IDs like "material_1766495512_690dcb35"
                    filt['material_id'] = material_id
            except Exception as e:
                print(f"material_id format error: {e}, using as string")
                filt['material_id'] = material_id
        
        print(f"Querying questions with filter: {filt}")
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
                "created_at": u.get("created_at"),
                "updated_at": u.get("updated_at")
            })
        
        print(f"Question search results: Found {len(results)} questions")
        return jsonify({"questions": results}), 200
        
    except Exception as e:
        print(f"Error in get_question: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Submit Student Answers
@db_bp.route('/student-answers-submit', methods=['POST'])
@jwt_required()
def submit_student_answers():
    try:
        data = request.get_json()
        student_id = data.get("student_id") if isinstance(data, dict) else None 
        if not student_id: 
            try: 
                student_id = get_jwt_identity() 
                print("submit_student_answers: using JWT identity as student_id:", student_id) 
            except Exception: 
                student_id = None
        material_id = data.get("material_id")
        answers = data.get("answers")  # Format: [{"question_id": "xxx", "user_answer": "xxx", "is_correct": true/false, "score": 10}]
        total_score = data.get("total_score")
        submission_time = data.get("submission_time", datetime.now().isoformat())

        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        if not material_id:
            return jsonify({"error": "material_id is required"}), 400
        if not answers:
            return jsonify({"error": "answers is required"}), 400

        # Handle student_id and material_id - can be ObjectId or string
        student_id_value = None
        if student_id:
            try:
                if len(student_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in student_id):
                    student_id_value = ObjectId(student_id)
                else:
                    student_id_value = student_id
            except:
                student_id_value = student_id

        material_id_value = None
        if material_id:
            try:
                if len(material_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in material_id):
                    material_id_value = ObjectId(material_id)
                else:
                    material_id_value = material_id
            except:
                material_id_value = material_id

        # Store answer record
        submission = {
            "student_id": student_id_value,
            "material_id": material_id_value,
            "answers": answers,
            "total_score": total_score,
            "submission_time": submission_time,
            "status": "submitted"
        }

        print(f"Inserting student answers submission: {submission}")
        res = db.student_answers.insert_one(submission)
        
        return jsonify({
            "_id": str(res.inserted_id),
            "message": "Student answers submitted successfully",
            "submission": submission
        }), 201

    except Exception as e:
        print(f"Error in submit_student_answers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Get Student Answers
@db_bp.route('/student-answers', methods=['GET'])
@jwt_required()
def get_student_answers():
    try:
        student_id = request.args.get('student_id')
        material_id = request.args.get('material_id')
        filt = {}
        
        # If student_id not provided, use JWT identity (useful for frontend) 
        if not student_id: 
            try: 
                student_id = get_jwt_identity() 
                print("get_student_answers: using JWT identity as student_id:", student_id) 
            except Exception: 
                student_id = None
        if student_id:
            try:
                if len(student_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in student_id):
                    filt['student_id'] = ObjectId(student_id)
                else:
                    filt['student_id'] = student_id
            except:
                filt['student_id'] = student_id
        
        if material_id:
            try:
                if len(material_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in material_id):
                    filt['material_id'] = ObjectId(material_id)
                else:
                    filt['material_id'] = material_id
            except:
                filt['material_id'] = material_id
        
        print(f"Querying student answers with filter: {filt}")
        submissions = list(db.student_answers.find(filt))
        
        results = []
        for s in submissions:
            results.append({
                "id": str(s["_id"]),
                "student_id": str(s.get("student_id")),
                "material_id": str(s.get("material_id")),
                "answers": s.get("answers"),
                "total_score": s.get("total_score"),
                "submission_time": s.get("submission_time"),
                "status": s.get("status")
            })
        
        print(f"Student answers search results: Found {len(results)} submissions")
        return jsonify({"submissions": results}), 200
        
    except Exception as e:
        print(f"Error in get_student_answers: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
