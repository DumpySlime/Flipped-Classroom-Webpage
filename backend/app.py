from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_pymongo import PyMongo
from gridfs import GridFS

from config import Config

app = Flask(__name__)

# Load configurations from Config class based on .env file
app.config.from_object(Config)

jwt = JWTManager(app)

try:
    mongo = PyMongo(app)
    db = mongo.db
    fs = GridFS(db)
    print("Database connected:", db)
except Exception as e:
    db = None
    fs = None
    print("Database connection error:", e)

CORS(app)

from routes.admin import admin_bp, init_db as init_admin_db
from routes.auth import auth_bp, init_db as init_auth_db
from routes.student import student_bp, init_db as init_student_db
from routes.teacher import teacher_bp, init_db as init_teacher_db
from routes.db import db_bp, init_db as init_db_db
from routes.llm import llm_bp, init_db as init_llm_db

# Initialize database for each blueprint
init_admin_db(db)
init_auth_db(db) 
init_student_db(db)
init_teacher_db(db)
init_db_db(db, fs)
init_llm_db(db, fs)

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(db_bp, url_prefix='/db')
app.register_blueprint(llm_bp, url_prefix='/llm')

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Flipped Classroom Backend"})

@app.route("/test-db")
def test_db():
    return jsonify({"message": f"Database connected: {db}"})

if __name__ == '__main__':
    app.run(debug=True)