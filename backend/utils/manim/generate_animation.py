import re
import sys
import os
import json
from pathlib import Path
import tempfile
import subprocess
import traceback

PROMPT_DIR = Path(__file__).parent / "prompt"
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv
from logger import setup_logging
from token_usage import get_token_usage

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

logger = setup_logging(current_file=Path(__file__).stem)

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

def clean_code(content: str) -> str:
    # Remove ```python ... ``` blocks, keeping only the code inside
    code_match = re.search(r'```(?:python)?\s*(.*?)```', content, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return content.strip()

def load_prompt(prompt_file: Path) -> str:
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: Prompt file not found: {prompt_file}")
        return None

def load_boilerplate() -> str:    
    boilerplate = load_prompt(PROMPT_DIR / "boilerplate_api_doc.txt")
    #high_level_boilerplate = load_prompt(PROMPT_DIR / "high_level_boilerplate.txt")
    #boilerplate = boilerplate.replace("{high_level_boilerplate.txt}", high_level_boilerplate)
    return boilerplate

def call_deepseek(system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 2000):
    if not DEEPSEEK_API_KEY:
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")
    if not DEEPSEEK_BASE_URL:
        raise Exception("DEEPSEEK_BASE_URL environment variable is not set")

    #logger.info(f"Calling Deepseek API with system prompt:\n {system_prompt}\n and user prompt:\n {user_prompt}")

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
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    response = session.post(
        f"{DEEPSEEK_BASE_URL}/v1/chat/completions", 
        headers=headers, 
        json=payload,
        timeout=60
    )
    response.raise_for_status()

    return response.json()

def call_storyboard(slide_text: str):
    storyboard_system_prompt = load_prompt(PROMPT_DIR / "storyboard_system_prompt.txt")
    storyboard_user_prompt_template = load_prompt(PROMPT_DIR / "storyboard_user_prompt.txt")

    if not storyboard_system_prompt or not storyboard_user_prompt_template:
        raise Exception("Could not load prompt files")
    
    storyboard_user_prompt = storyboard_user_prompt_template.replace("{SLIDE_TEXT}", slide_text)

    try:
        logger.info(f"Generating storyboard...")
        result = call_deepseek(storyboard_system_prompt, storyboard_user_prompt, 0.7, 2000)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", {})
        token_usage, total_tokens = get_token_usage(result)
        storyboard = json.loads(content)

        logger.info("Storyboard generated successfully")
        logger.info(f"Storyboard generated: {storyboard}")
        logger.info(f"Storyboard generated with token usage: {token_usage}")
        return storyboard, total_tokens
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Storyboard generation failed: {e}")
        return None, None

def call_animation(storyboard):    
    system_prompt = load_prompt(PROMPT_DIR / "manim_code_system_prompt.txt")
    boilerplate = load_boilerplate()
    user_prompt_template = load_prompt(PROMPT_DIR / "manim_code_user_prompt.txt")

    if not system_prompt or not boilerplate or not user_prompt_template:
        logger.error("Could not load system prompt file for animation generation")
        raise Exception("Could not load prompt files")
    
    system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
    user_prompt = user_prompt_template.replace("{STORYBOARD}", json.dumps(storyboard))

    try:
        logger.info(f"Generating animation code...")
        result = call_deepseek(system_prompt, user_prompt, 0.5, 5000)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        clean_content = clean_code(content)
        token_usage, total_tokens = get_token_usage(result)
    
        logger.info("Manim code generated successfully")
        logger.info(f"Code generated: {clean_content}")
        logger.info(f"Manim code generated with token usage: {token_usage}")
        return clean_content, total_tokens
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Animation generation failed: {e}")
        return None, None

def review_animation_code(manim_code: str, storyboard):
    """Review generated Manim code against storyboard."""
    system_prompt = load_prompt(PROMPT_DIR / "code_review_system_prompt.txt")
    boilerplate = load_boilerplate()
    system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
    user_prompt = load_prompt(PROMPT_DIR / "code_review_user_prompt.txt")
    user_prompt = user_prompt.replace("{MANIM_CODE}", manim_code)
    user_prompt = user_prompt.replace("{STORYBOARD}", json.dumps(storyboard))

    try:
        logger.info(f"Reviewing code...")
        result = call_deepseek(system_prompt, user_prompt, 0.5, 5000)
        logger.info("Code review completed successfully")
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        clean_content = clean_code(content)
        logger.info(f"Code review result: {clean_content}")
        token_usage, total_tokens = get_token_usage(result)
        logger.info(f"Code review token usage: {token_usage}")
        return clean_content, total_tokens
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        return None, None

def generate_animation(slide_text: str, review_code: bool = True):
    print("DEBUG in generate_animation, full slide_text:\n", slide_text)
    if not slide_text:
        logger.warning("Empty slide text provided")
        return None

    storyboard, storyboard_tokens = call_storyboard(slide_text)
    if storyboard is None:
        logger.error("Failed to generate storyboard, skipping animation generation")
        return None

    manim_code, manim_tokens = call_animation(storyboard)
    if manim_code is None:
        logger.error("Failed to generate manim code from storyboard")
        return None

    review_tokens = 0
    if review_code:
        reviewed_code, review_tokens = review_animation_code(manim_code, storyboard)
        if reviewed_code is None:
            logger.error("Code review failed, using unreviewed manim_code")
        else:
            manim_code = reviewed_code

    total = storyboard_tokens + manim_tokens + (review_tokens or 0)
    logger.info(f"Animation generated with total tokens: {total}")
    return manim_code


if __name__ == "__main__":
    # Example usage
    test_slide = """
        A polygon is a closed shape with straight sides
        All sides connect end-to-end to form a single closed path
        Polygons are named by how many sides they have
    """
    generate_animation(test_slide)
