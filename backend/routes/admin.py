from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt


db = None

def init_db(mongo):
    global db
    db = mongo.db

admin_bp = Blueprint('admin', __name__)

def hash_password(password):
    return Bcrypt().generate_password_hash(password).decode('utf-8')

def admin_auth():
    current_user_id = get_jwt_identity()
    current_user = db.users.find_one({"_id": ObjectId(current_user_id)})
    if not current_user or current_user.get('role', '').lower() == "admin":
        return jsonify({"error": "Admin access is required"}), 403

@admin_bp.route('/api/register', methods=['POST'])
@jwt_required()
def register():
    try:
        admin_auth()
        user_info = request.json

        # Validation
        required_fields = ["username", "password", "role", "firstName", "lastName"]
        for field in required_fields:
            if field not in user_info:
                return jsonify({"error": f"{field} is required"}), 400

        # Check if user already exists
        if db.users.find_one({"username": user_info["username"]}):
            return jsonify({"error": "User already exists"}), 409

        # Hash password and create user
        hashed_password = hash_password(user_info["password"])

        # Create user object
        user = {
            "username": user_info["username"],
            "password": hashed_password,
            "role": user_info["role"],
            "firstName": user_info["firstName"],
            "lastName": user_info["lastName"]
        }
        result = db.users.insert_one(user)

        # Create tokens
        access_token = create_access_token(identity=str(result.inserted_id))
        refresh_token = create_refresh_token(identity=str(result.inserted_id))

        response_user = {
            "id": str(result.inserted_id),
            "username": user["username"],
            "role": user["role"],
            "firstName": user["firstName"],
            "lastName": user["lastName"]
        }

        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": response_user
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        admin_auth()
        users = db.users.find()
        user_list = []
        for user in users:
            user['_id'] = str(user['_id'])
            user_list.append(user)
        return jsonify({"users": user_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500