from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create Flask app for database connection
app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/flipped_classroom")

# Initialize MongoDB connection
db = None
try:
    mongo = PyMongo(app)
    db = mongo.db
    print("Database connected successfully")
except Exception as e:
    print(f"Database connection error: {e}")
    print("MongoDB server may not be running. Please start MongoDB and try again.")
    print("Current login functionality uses mock data since real database connection failed.")

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt(app)

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def seed_database():
    """Seed the database with initial user data"""
    
    # Check if database connection is established
    if db is None:
        print("Cannot seed database - no connection available.")
        return
        
    # Check if users collection exists and is not empty
    if db.user.count_documents({}) > 0:
        print("Users collection already has data. Skipping seeding.")
        return
    
    # Create initial teacher user
    teacher = {
        "username": "teacher",
        "password": hash_password("teacher"),
        "role": "teacher",
        "firstName": "Sarah",
        "lastName": "Johnson"
    }
    
    # Create initial student user
    student = {
        "username": "student",
        "password": hash_password("student"),
        "role": "student",
        "firstName": "John",
        "lastName": "Doe"
    }
    
    # Insert users into database
    teacher_result = db.user.insert_one(teacher)
    student_result = db.user.insert_one(student)
    
    print(f"Successfully seeded database with initial users:")
    print(f"- Teacher: {teacher['firstName']} {teacher['lastName']} (username: {teacher['username']})")
    print(f"- Student: {student['firstName']} {student['lastName']} (username: {student['username']})")
    print(f"Passwords are 'teacher' and 'student' respectively")

if __name__ == "__main__":
    with app.app_context():
        seed_database()