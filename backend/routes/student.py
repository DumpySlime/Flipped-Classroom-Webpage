from flask import Blueprint

db = None

def init_db(mongo):
    global db
    db = mongo.db

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return {"message": "Welcome to the Student Dashboard"}

@student_bp.route('/materials', methods=['GET'])
def materials():
    return {"message": "Welcome to the Student Materials"}

@student_bp.route('/chatbot', methods=['GET'])
def chatbot():
    return {"message": "Welcom to Chatbot"}