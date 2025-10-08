import bson

from flask import current_app, g
from werkzeug.local import LocalProxy
from flask_pymongo import PyMongo
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

mongo = PyMongo()

# Get all users
def get_all_user():
    try:
        teachers = db.teacher.find({})
        students = db.student.find({})
        return teachers, students
    except Exception as e:
        return e

# Get user by username and password    
def get_user_by_id_and_pw(username, pw):
    try:
        teacher = db.teacher.find_one({"username": username, "password": pw})
        student = db.student.find_one({"username": username, "password": pw})
        if teacher is not None:
            return teacher, "teacher"
        elif student is not None:
            return student, "student"
        else:
            return None, None
    except Exception as e:
        return e, None
