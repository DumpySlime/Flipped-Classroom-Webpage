from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient('localhost', 27017)

db = client.flask_database



@app.route('/')
def index():
    return jsonify({"message": "Flipped Classroom Backend"})

if __name__ == '__main__':
    app.run(debug=True)