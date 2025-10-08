from flask import Blueprint

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
def dashboard():
    return {"message": "Welcome to the Student Dashboard"}
