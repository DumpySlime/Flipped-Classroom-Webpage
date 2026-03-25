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
import time

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

logger = setup_logging(current_file=Path(__file__).stem)

# --- Utility Functions ---

def get_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    respect_retry_after_header=False,
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
        timeout=600
    )
    response.raise_for_status()

    return response.json()

def call_storyboard(title: str, slide_text: str, language: str):
    storyboard_system_prompt = load_prompt(PROMPT_DIR / "storyboard_system_prompt.txt")
    storyboard_user_prompt = load_prompt(PROMPT_DIR / "storyboard_user_prompt.txt")

    if not storyboard_system_prompt or not storyboard_user_prompt:
        raise Exception("Could not load prompt files")
    
    storyboard_user_prompt = storyboard_user_prompt.replace("{SLIDE_TEXT}", slide_text)
    storyboard_user_prompt = storyboard_user_prompt.replace("{SLIDE_TITLE}", title)
    storyboard_system_prompt = storyboard_system_prompt.replace("{LANGUAGE}", language)

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

def call_animation(storyboard, language: str, title: str):    
    system_prompt = load_prompt(PROMPT_DIR / "manim_code_system_prompt.txt")
    boilerplate = load_boilerplate()
    user_prompt = load_prompt(PROMPT_DIR / "manim_code_user_prompt.txt")

    if not system_prompt or not boilerplate or not user_prompt:
        logger.error("Could not load system prompt file for animation generation")
        raise Exception("Could not load prompt files")
    
    system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
    system_prompt = user_prompt.replace("{LANGUAGE}", language)
    system_prompt = system_prompt.replace("{SLIDE_TITLE}", title)
    user_prompt = user_prompt.replace("{STORYBOARD}", json.dumps(storyboard))

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

def review_animation_code(manim_code: str, storyboard, title: str, language: str):
    """Review generated Manim code against storyboard."""
    system_prompt = load_prompt(PROMPT_DIR / "code_review_system_prompt.txt")
    boilerplate = load_boilerplate()
    system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
    system_prompt = system_prompt.replace("{LANGUAGE}", language)
    system_prompt = system_prompt.replace("{SLIDE_TITLE}", title)
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
    
def generate_animation(title: str, slide_text: str, language: str):
    print(f"DEBUG in generate_animation, slide title:\n{title}\nfull slide_text:\n{slide_text}\nLanguage: {language}")
    if not slide_text:
        logger.warning("Empty slide text provided")
        return None
    start_time = time.time()
    storyboard, storyboard_tokens = call_storyboard(title, slide_text, language)
    if storyboard is None:
        logger.error("Failed to generate storyboard, skipping animation generation")
        return None

    manim_code, manim_tokens = call_animation(storyboard, language, title)
    if manim_code is None:
        logger.error("Failed to generate manim code from storyboard")
        return None

    total_review_tokens = 0
    for i in range(4):  # Retry up to 3 times if validation fails
        logger.info(f"Validating generated code.")
        reviewed_code, review_tokens = review_animation_code(manim_code, storyboard, title, language)
        validation = validate_code(reviewed_code)
        total_review_tokens += review_tokens
        if validation:
            break
        logger.warning(f"Validation failed, Attempt {i+1}/3")
        if i == 3:  # If all retries failed, return error code
            logger.error("Failed to generate valid animation code after 3 attempts")
            reviewed_code = """
            from scene import CScene
            import numpy as np

            class GeneratedScene(CScene):
                def construct(self):
                    title = self.setup_scene("Failed Animation")
            """

    total_time = time.time() - start_time
    total_token = storyboard_tokens + manim_tokens + total_review_tokens
    logger.info(f"Animation generated with total tokens: {total_token}")
    logger.info(f"Total generation time: {total_time:.2f}s")
    return reviewed_code, total_token, total_time


if __name__ == "__main__":
    # Example usage
    test_slide = """
對於任意銳角θ，可構造直角三角形：對邊/斜邊 = sinθ，鄰邊/斜邊 = cosθ，對邊/鄰邊 = tanθ
已知一邊一角時，可用畢氏定理求其他邊長
例如：若sinθ = 3/5，則可設對邊=3，斜邊=5，計算鄰邊=4
從而得到cosθ = 4/5，tanθ = 3/4
    """

    test_title = "利用直角三角形推導三角比"
    reviewed_code, total_token, time = generate_animation(test_title, test_slide, language='Chinese')
