from flask import Blueprint

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/dashboard')
def dashboard():
    return {"message": "Welcome to the Teacher Dashboard"}
