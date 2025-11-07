from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from gridfs import GridFS
import io
from datetime import datetime

db = None
fs = None

def init_db(db_instance, fs_instance):
    global db
    db = db_instance
    global fs
    fs = fs_instance

llm_bp = Blueprint('llm', __name__)

llm_bp.route('/api/llm/query', methods=['GET'])
@jwt_required()
def llm_query():
    try:
        subject = request.args.get('subject')
        topic = request.args.get('topic')
        instruction = request.args.get('instruction')
    except Exception as e:
        return {"error": str(e)}, 500
