from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_cors import CORS

auth_bp = Blueprint('auth', __name__)

cors = CORS(auth_bp)

@auth_bp.route('/api/users', methods=['GET'])
def users():
    return jsonify(
        {
            "users": [
                {"id": 1, "name": "User 1", "email": "user1@example.com"},
                {"id": 2, "name": "User 2", "email": "user2@example.com"},
            ]
        }
    )

@auth_bp.rout('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == 'test' and password == 'test':
        access_token = create_access_token(identity={'username': username})
        refresh_token = create_refresh_token(identity={'username': username})
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    else:
        return jsonify({"msg": "Bad username or password"}), 401

if __name__ == '__main__':
    auth_bp.run(debug=True)