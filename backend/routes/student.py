from flask import Blueprint
from flask_jwt_extended import jwt_required

db = None

def init_db(mongo):
    global db
    db = mongo.db

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return {"message": "Welcome to the Student Dashboard"}

@student_bp.route('/materials', methods=['GET'])
@jwt_required()
def materials():
    return {"message": "Welcome to the Student Materials"}

@student_bp.route('/chatbot', methods=['GET'])
@jwt_required()
def chatbot():
    return {"message": "Welcome to Chatbot"}