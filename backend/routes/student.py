from flask import Blueprint
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
def dashboard():
    return {"message": "Welcome to the Student Dashboard"}

@student_bp.route('/materials', methods=['GET'])
def materials():
    return {"message": "Welcome to the Student Materials"}

@student_bp.route('/chatbot', methods=['GET'])
def chatbot():

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
        ],
        stream=False
    )

    print(response.choices[0].message.content)

    return {"message": "Welcome to Chatbot"}