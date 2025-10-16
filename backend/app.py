from flask import Flask, jsonify
import logging
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_pymongo import PyMongo
import os

from config import Config

app = Flask(__name__)

# Load configurations from Config class based on .env file
app.config.from_object(Config)

jwt = JWTManager(app)

app.logger.setLevel(logging.INFO)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set media and temporary directories with fallback to local paths
"""if os.environ.get('DOCKER_ENV'):
    app.config['MEDIA_DIR'] = os.getenv('MEDIA_DIR', '/app/media')
    app.config['TEMP_DIR'] = os.getenv('TEMP_DIR', '/app/tmp')
else:"""
app.config['MEDIA_DIR'] = os.path.join(os.path.dirname(__file__), 'media')
app.config['TEMP_DIR'] = os.path.join(os.path.dirname(__file__), 'tmp')

# Ensure directories exist
os.makedirs(app.config['MEDIA_DIR'], exist_ok=True)
os.makedirs(app.config['TEMP_DIR'], exist_ok=True)
os.makedirs(os.path.join(app.config['MEDIA_DIR'], 'videos', 'scene', '720p30'), exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'videos'), exist_ok=True)

try:
    mongo = PyMongo(app)
    db = mongo.db
    #print("Database connected:", db)
except Exception as e:
    print("Database connection error:", e)
    db = None

CORS(app)

from routes.admin import admin_bp, init_db as init_admin_db
from routes.auth import auth_bp, init_db as init_auth_db
from routes.student import student_bp, init_db as init_student_db
from routes.teacher import teacher_bp, init_db as init_teacher_db
from routes.manim import mat_bp

# Initialize database for each blueprint
init_admin_db(mongo)
init_auth_db(mongo) 
init_student_db(mongo)
init_teacher_db(mongo)

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(mat_bp, url_prefix='/materials')

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Flipped Classroom Backend"})

@app.route("/test-db")
def test_db():
    return jsonify({"message": f"Database connected: {db}"})

if __name__ == '__main__':
    app.run(debug=True)