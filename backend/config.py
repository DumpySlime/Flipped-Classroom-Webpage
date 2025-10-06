import os
from datetime import timedelta
from dotenv import load_dotenv, find_dotenv

def load_env_files() -> str:
    """Load environment variables from .env files."""
    base_env_path = find_dotenv(".env", usecwd=True, raise_error_if_not_found=False)
    if base_env_path:
        load_dotenv(base_env_path, override=False)

    env_name = os.environ.get("APP_ENV", "development").lower
    env_specific = f".env.{env_name}"
    env_specific_path = find_dotenv(env_specific, usecwd=True, raise_error_if_not_found=False)
    if env_specific_path:
        load_dotenv(env_specific_path, override=True)

    return env_name

class BaseConfig:
    """Base configuration with default settings."""
    # Mongo
    MONGO_URL = os.environ.get("MONGO_URL")

def get_config_class():
    """Resolve env, load env files, and return the config class for Flask"""
    env = load_env_files()
    return env