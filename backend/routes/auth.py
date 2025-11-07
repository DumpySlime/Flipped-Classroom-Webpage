from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity
)
from flask_bcrypt import Bcrypt
from datetime import datetime

db = None

def init_db(db_instance):
    global db
    db = db_instance

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    return Bcrypt().generate_password_hash(password).decode('utf-8')

def check_password(password, hashed):
    return Bcrypt().check_password_hash(hashed, password)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    try:
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
            "lastName": user_info["lastName"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
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

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        username = request.json["username"]
        password = request.json["password"]

        # Validation
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Checks if user exists in database
        user = db.users.find_one({"username": username})
        if not user or not check_password(password, user['password']):
            return jsonify({"error": "Invalid username or password"}), 401

        if not check_password(password, user['password']):
            return jsonify({"error": "Invalid username or password"}), 401

        access_token = create_access_token(identity=str(user['_id']))
        refresh_token = create_refresh_token(identity=str(user['_id']))

        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "role": user['role'],
                "firstName": user['firstName'],
                "lastName": user['lastName'],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@auth_bp.route("/test-login", methods=['GET'])
@jwt_required()
def test_login():
    return jsonify({"message": "Login successful",
                    "user": get_jwt_identity()}), 200