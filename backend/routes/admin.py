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
@jwt_required()
def admin_auth():
    current_user_id = get_jwt_identity()
    current_user = db.users.find_one({"_id": ObjectId(current_user_id)})
    if not current_user or current_user.get('role', '').lower() == "admin":
        return jsonify({"error": "Admin access is required"})