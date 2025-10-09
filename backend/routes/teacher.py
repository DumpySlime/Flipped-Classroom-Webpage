from flask import Blueprint

teacher_bp = Blueprint('teacher', __name__)

# Teacher Dashboard
@teacher_bp.route('/dashboard')
def dashboard():
    return {"message": "Welcome to the Teacher Dashboard"}

# Teacher Materials
@teacher_bp.route('/materials')
def materials():
    return {"message": "Welcome to the Teacher Materials"}

# Teacher Video Generation
@teacher_bp.route('/material_generation')
def generate():
    return {"message": "Welcome to Material Generation"}