from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS

from dotenv import load_dotenv
import os

# take environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# Flask
app.config["DEBUG"] = False
app.config["TESTING"] = False
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", "true")

try:
    mongo = PyMongo(app)
    db = mongo.db
    print("Database connected:", db)
except Exception as e:
    print("Database connection error:", e)
    db = None