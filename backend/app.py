from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_pymongo import PyMongo
from gridfs import GridFS
from config import Config

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
     origins=["http://localhost:3000", "http://localhost:3005", "https://flippedclassroom.ngrok-free.app"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     resources={
         r"/api/*": {"origins": "*"},
         r"/db/*": {"origins": "*"},
         r"/auth/*": {"origins": "*"}
     })

from routes.admin import admin_bp, init_db as init_admin_db
from routes.auth import auth_bp, init_db as init_auth_db
from routes.db import db_bp, init_db as init_db_db
from routes.llm import llm_bp, init_db as init_llm_db
from routes.ai import ai_bp
from routes.analytics import analytics_bp, init_analytics  


init_admin_db(db)
init_auth_db(db)
init_db_db(db, fs)
init_llm_db(db, fs)
init_analytics(db) 

app.register_blueprint(ai_bp, url_prefix='/api/ai')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(db_bp, url_prefix='/db')
app.register_blueprint(llm_bp, url_prefix='/api/llm')
app.register_blueprint(analytics_bp)  

@app.route('/')
def index():
    return jsonify({
        "message": "Flipped Classroom API",
        "status": "running",
        "database": db.name if db is not None else "Not connected"
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Flipped Classroom Backend Starting...")
    print(f"Database: {db.name if db is not None else 'Not connected'}")
    print(f"CORS: Enabled for localhost:3000, 3005")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
