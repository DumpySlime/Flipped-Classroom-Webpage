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
        return None

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
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip("```python").strip("```").strip()
        token_usage, total_tokens = get_token_usage(result)
    
        logger.info("Manim code generated successfully")
        logger.info(f"Code generated: {content}")
        logger.info(f"Manim code generated with token usage: {token_usage}")
        return content, total_tokens
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Animation generation failed: {e}")
        return None

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
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip("```python").strip("```").strip()
        logger.info(f"Code review result: {content}")
        token_usage, total_tokens = get_token_usage(result)
        logger.info(f"Code review token usage: {token_usage}")
        return content, total_tokens
    except Exception as e:
        logger.error(f"Code review failed: {e}")
        return None

def validate_code(cscene_code: str) -> bool:
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
        logger.info(f"Validating code by writing to temporary file: {tf.name}\n Code content:\n{cscene_code}")
        tf.write(cscene_code.encode('utf-8'))
        tf.flush()
        try:
            cmd = [
                sys.executable, "-m", "manim", "render",
                tf.name,
                "--dry_run",
                "--disable_caching",
                "-v", "WARNING",  # Minimal logs
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Manim dry-run failed:\n{result.stderr}")
                return False
                
            logger.info("Dry-run passed - code is safe!")
            return True

            
        except subprocess.TimeoutExpired:
            logger.error("Manim dry-run timed out")
            return False
        except Exception as e:
            logger.error(f"Validation error: {traceback.format_exc()}")
            return False


def generate_animation(slide_text: str) -> str:
    total_tokens = 0
    if not slide_text:
        logger.warning("Empty slide text provided")
        return None        
    logger.info(f"Generating animation for slide text: {slide_text}")
    storyboard, storyboard_tokens = call_storyboard(slide_text)
    total_tokens += storyboard_tokens
    if storyboard:
        manim_code, manim_tokens = call_animation(storyboard)
        total_tokens += manim_tokens
        for i in range(3):  # Retry up to 3 times if validation fails
            validation = validate_code(manim_code)
            if validation:
                break
            logger.warning(f"Validation failed for generated code. Attempt {i+1}/3")
            manim_code, review_tokens = review_animation_code(manim_code, storyboard)
            total_tokens += review_tokens
            if i == 2:  # If all retries failed, return error code
                logger.error("Failed to generate valid animation code after 3 attempts")
                manim_code = """
                from scene import CScene
                import numpy as np

                class GeneratedScene(CScene):
                    def construct(self):
                        title = self.setup_scene("Failed Animation")
                """
        logger.info(f"Animation generated with total tokens: {total_tokens}")

        return manim_code
    else:
        logger.error("Failed to generate storyboard, skipping animation generation")
        return None