from flask import request, jsonify
from config import app, db

from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.student import student_bp
from routes.teacher import teacher_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(teacher_bp, url_prefix='/teacher')

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Flipped Classroom Backend"})

@app.route("/test-db")
def test_db():
    print("Database connected:", db)
    return "Check console for db object"

if __name__ == '__main__':
    app.run(debug=True)