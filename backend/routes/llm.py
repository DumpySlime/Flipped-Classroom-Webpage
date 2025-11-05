from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from gridfs import GridFS
import io
from datetime import datetime

db = None
fs = None

def init_db(db_instance, fs_instance):
    global db
    db = db_instance
    global fs
    fs = fs_instance

llm_bp = Blueprint('llm', __name__)