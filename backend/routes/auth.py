from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token
)
from flask_bcrypt import Bcrypt

db = None

def init_db(mongo):
    global db
    db = mongo.db

auth_bp = Blueprint('auth', __name__)

def check_password(password, hashed):
    return Bcrypt().check_password_hash(hashed, password)

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
                "lastName": user['lastName']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500