import sys
import os
import json
from pathlib import Path

PROMPT_DIR = Path(__file__).parent / "prompt"
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv

load_dotenv()

import logging

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

# --- Utility Functions ---


def get_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504, 429),
    session=None,
) -> requests.Session:
    """Custom retry logic for API calls."""
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def load_prompt(prompt_file: Path) -> str:
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: Prompt file not found: {prompt_file}")
        return None

def call_storyboard(slide_text: str):
    if not DEEPSEEK_API_KEY:
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")
    
    # Load prompts
    storyboard_system_prompt = load_prompt(PROMPT_DIR / "storyboard_system_prompt.txt")
    storyboard_user_prompt_template = load_prompt(PROMPT_DIR / "storyboard_user_prompt.txt")

    if not storyboard_system_prompt or not storyboard_user_prompt_template:
        raise Exception("Could not load prompt files")
    
    # Format user prompt with slide text
    storyboard_user_prompt = storyboard_user_prompt_template.replace("{SLIDE_TEXT}", slide_text)

    try:
        session = get_session()
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": storyboard_system_prompt
                },
                {
                    "role": "user",
                    "content": storyboard_user_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": {
                "type": "json_object"
            }
        }

        logging.info(f"Generating storyboard with Slide text: {slide_text}")
        response = session.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions", 
            headers=headers, 
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", {})
        token_usage = result.get("usage", {})
        storyboard = json.loads(content)
        logging.info(f"Storyboard generated: {content}")
        logging.info(f"Storyboard generated with token usage: {token_usage}")
        return storyboard
    
    except Exception as e:
        logging.error(f"Storyboard generation failed: {e}")
        return None

def call_animation(storyboard):
    if not DEEPSEEK_API_KEY:
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")
    
    system_prompt = load_prompt(PROMPT_DIR / "animation_system_prompt.txt")
    user_prompt_template = load_prompt(PROMPT_DIR / "animation_user_prompt.txt")


if __name__ == "__main__":
    logging.basicConfig(filename='logs/generate_animation.log', level=logging.INFO)
    # Example usage
    test_slide = """
        A polygon is a closed shape with straight sides
        All sides connect end-to-end to form a single closed path
        Polygons are named by how many sides they have
    """
    storyboard_result = call_storyboard(test_slide)
    print(json.dumps(storyboard_result, indent=2))