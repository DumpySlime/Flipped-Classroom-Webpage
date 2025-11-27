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
    # Using sensible defaults in case environment variables are missing
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # Default 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES", 86400))  # Default 1 day

    # DeepSeek (LLM) Configuration - Updated to replace OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")

    # Office Web Viewer
    OFFICE_SECRET_KEY = os.environ.get("OFFICE_SECRET_KEY")
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL")
    
    # XF PPTv2
    XF_PPT_APP_ID = os.environ.get("XF_PPT_APP_ID")
    XF_PPT_SECRET = os.environ.get("XF_PPT_SECRET")
    XF_PPT_BASE_URL = os.environ.get("XF_PPT_BASE_URL")
