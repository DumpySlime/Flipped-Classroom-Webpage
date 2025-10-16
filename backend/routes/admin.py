from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
import bcrypt


db = None

def init_db(mongo):
    global db
    db = mongo.db

admin_bp = Blueprint('admin', __name__)

def admin_auth():
    current_user_id = get_jwt_identity()
    current_user = db.users.find_one({"_id": ObjectId(current_user_id)})
    if not current_user or current_user.get('role', '').lower() == "admin":
        return jsonify({"error": "Admin access is required"})
    
@admin_bp.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = db.users.find()
        user_list = []
        for user in users:
            user['_id'] = str(user['_id'])
            user_list.append(user)
        return jsonify({"users": user_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500