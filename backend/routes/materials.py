from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import io
from datetime import datetime

db = None
fs = None

def init_db(db_instance, fs_instance):
    global db
    db = db_instance
    global fs
    fs = fs_instance

materials_bp = Blueprint('materials', __name__)

@materials_bp.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_material():
    # Handle file upload
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
    
    identity = get_jwt_identity()
    try:
        uploader_id = ObjectId(identity)
    except Exception as e:
        return {"error": "Invalid user identity in token"}, 400
    
    user = db.users.find_one({'_id': uploader_id})
    if not user:
        return {"error": "User not found"}, 404

    metadata = {
        'subject': subject,
        'topic': topic,
        'uploaded_by': user['_id'],
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
        'uploaded_by': user['_id'],
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
            "uploaded_by": str(uploader_id),
            "upload_date": gf.upload_date.isoformat(),
            "size_bytes": gf.length,
            "content_type": gf.content_type
        }),201
    return jsonify({'result': 'Error occurred during uploading'}),500

@materials_bp.route('/api/materials/<material_id>', methods=['GET'])
@jwt_required()
def get_material(material_id):
    try:
        mat = db.materials.find_one({'_id': ObjectId(material_id)})
        if not mat:
            return {"error": "Material not found"}, 404
        
        gf = fs.get(mat['file_id'])
        return send_file(
            io.BytesIO(gf.read()),
            download_name=gf.filename,
            mimetype=gf.content_type,
            as_attachment=True
        )
    except Exception as e:
        return {"error": str(e)}, 500

