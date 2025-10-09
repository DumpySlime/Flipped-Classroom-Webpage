from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
import bcrypt
from config import db

auth_bp = Blueprint('auth', __name__)

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        # Validation
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password are required"}), 400

        user = db.user.find_one({"username": data['username']})
        if not user or not check_password(data['password'], user['password']):
            return jsonify({"error": "Invalid username or password"}), 401

        if not check_password(data['password'], user['password']):
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