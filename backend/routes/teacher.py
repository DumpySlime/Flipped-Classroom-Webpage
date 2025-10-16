from flask import Blueprint
from flask_jwt_extended import jwt_required

db = None

def init_db(mongo):
    global db
    db = mongo.db

teacher_bp = Blueprint('teacher', __name__)

# Teacher Dashboard
@teacher_bp.route('/dashboard')
def dashboard():
    return {"message": "Welcome to the Teacher Dashboard"}

# Teacher Materials
@teacher_bp.route('/materials')
@jwt_required()
def materials():
    return {"message": "Welcome to the Teacher Materials"}

# Teacher Video Generation
@teacher_bp.route('/material_generation')
@jwt_required()
def generate():
    return {"message": "Welcome to Material Generation"}