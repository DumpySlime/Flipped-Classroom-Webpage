# app.py 
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_pymongo import PyMongo
from gridfs import GridFS
from config import Config
# Removed the unnecessary 'from routes.llm import generate_llm_content' import 
# since the analytics route now handles the LLM call internally.
# The llm blueprint itself is still imported below.

app = Flask(__name__)
app.config.from_object(Config)

jwt = JWTManager(app)

db = None
fs = None

try:
    mongo = PyMongo(app)
    db = mongo.db
    fs = GridFS(db)
    print("Database connected:", db.name)
except Exception as e:
    print("Database connection error:", e)

CORS(app, 
     origins=["http://localhost:3005", "https://flippedclassroom.ngrok-free.app"],
     supports_credentials=True,  # Allow cookies/auth headers
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     resources={r"/api/*": {"origins": "http://localhost:3005"}})

# Import all routes
from routes.admin import admin_bp, init_db as init_admin_db
from routes.auth import auth_bp, init_db as init_auth_db
from routes.db import db_bp, init_db as init_db_db
from routes.llm import llm_bp, init_db as init_llm_db
from routes.ai import ai_bp
from routes.analytics import analytics_bp, init_db as init_analytics_db 

# Init DB for all blueprints
init_admin_db(db)
init_auth_db(db) 
init_db_db(db, fs)
init_llm_db(db, fs)
init_analytics_db(db) 

# Register Blueprints
app.register_blueprint(ai_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(db_bp, url_prefix='/api/db')
app.register_blueprint(llm_bp, url_prefix='/api')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics') 


if __name__ == '__main__':
    # Set host='0.0.0.0' for deployment/ngrok compatibility
    app.run(debug=True, host='0.0.0.0', port=5000)