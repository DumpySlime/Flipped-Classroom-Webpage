# app.py - 香港 02:12 AM 最終版
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_pymongo import PyMongo
from gridfs import GridFS
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

jwt = JWTManager(app)

try:
    mongo = PyMongo(app)
    db = mongo.db
    fs = GridFS(db)
    print("Database connected:", db.name)
except Exception as e:
    db = None
    fs = None
    print("Database connection error:", e)

CORS(app, 
     origins=["http://localhost:3005", "https://flippedclassroom.ngrok-free.app"],
     supports_credentials=True,  # Allow cookies/auth headers
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],   # 關鍵！允許 cookie + 3005 port
     resources={r"/api/*": {"origins": "http://localhost:3005"}},
     supports_credentials=True)

# Import 所有 routes
from routes.admin import admin_bp, init_db as init_admin_db
from routes.auth import auth_bp, init_db as init_auth_db
from routes.db import db_bp, init_db as init_db_db
from routes.llm import llm_bp, init_db as init_llm_db
from routes.ai import ai_bp                          # 已 import

# Init DB
init_admin_db(db)
init_auth_db(db) 
init_db_db(db, fs)
init_llm_db(db, fs)

# 關鍵！register AI blueprint
app.register_blueprint(ai_bp)                        # 加返呢行！
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(db_bp, url_prefix='/db')
app.register_blueprint(llm_bp, url_prefix='/llm')

@app.route('/')
def index():
    return jsonify({"message": "Flipped Classroom - HK AI POWERED!", "time": "2025-11-11 02:12 HKT"})

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "ai_chat": True, "grok": "ready", "hongkong": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')