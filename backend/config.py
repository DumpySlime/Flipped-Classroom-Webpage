from dotenv import load_dotenv
import os

# take environment variables from .env
load_dotenv()

class Config:
    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI")

    # Flask
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "true")
    TESTING = False
    DEBUG = False

    # JWT
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES"))  # Default 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES"))  # Default 1 day

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
