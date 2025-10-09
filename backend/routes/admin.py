from flask import Blueprint, jsonify, request
#from flask_jwt_extended import jwt_required, get_jst_identity
from config import db
from bson.objectid import ObjectId
import bcrypt

admin_bp = Blueprint('admin', __name__)
"""
def admin_auth():
    current_user_id = get_jst_identity()
    current_user = db.users.fine_one({"_id": ObjectId(current_user_id)})
    if not current_user or current_user.get('role', '').lower() == "admin":
        return jsonify({"error": "Admin access is required"})
"""
@admin_bp.route('/api/add-user', methods=["POST"])
#@jwt_required
def add_user():
    try:
        #admin_auth()
        data = request.json
        # Validate required fields
        required_fields = ['username', 'password', 'role', 'firstName', 'lastName']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Check if username exists
        if db.users.find_one({"username": data['username']}):
            return jsonify({"error": "Username already exists"}), 400
        
        # Insert new user
        new_user ={
            "username": data['username'],
            "password": bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()),
            "role": data['role'],
            "firstName": data['firstName'],
            "lastName": data['lastName']
        }
        
        db.users.insert_one(new_user)
        return jsonify({"message": "User added successfully"}),
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
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