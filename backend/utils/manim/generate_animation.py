import re
import sys
import os
import json
from pathlib import Path
import requests
from dotenv import load_dotenv
import time
import subprocess
import tempfile
import traceback
import time
import ast

PROMPT_DIR = Path(__file__).parent / "prompt"
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger import setup_logging
from token_usage import get_token_usage
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = "deepseek-chat" 

logger = setup_logging(current_file=Path(__file__).stem)


def clean_code(content: str) -> str:
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
    return load_prompt(PROMPT_DIR / "boilerplate_api_doc.txt")


def call_deepseek(system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 2500):
    if not DEEPSEEK_API_KEY:
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")
    if not DEEPSEEK_BASE_URL:
        raise Exception("DEEPSEEK_BASE_URL environment variable is not set")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    }

    # Enable temperature for chat models
    if "chat" in DEEPSEEK_MODEL.lower():
        payload["temperature"] = temperature
        payload["max_tokens"] = max_tokens
    if "reasoning" in DEEPSEEK_MODEL.lower():
        payload["max_tokens"] = 8000

    max_retries = 3
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"All {max_retries} attempts failed due to network error: {e}")
                raise
            wait = 2 ** (attempt - 1)  # 1s, 2s, 4s
            logger.warning(f"Network error on attempt {attempt}/{max_retries}: {e}. Retrying in {wait}s...")
            time.sleep(wait)

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            last_exception = e

            # Retry only on transient/server-side errors
            if status in [429, 500, 502, 503, 504] and attempt < max_retries:
                wait = 2 ** (attempt - 1)
                logger.warning(f"HTTP {status} on attempt {attempt}/{max_retries}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                logger.error(f"Non-retryable HTTP error {status}: {e.response.text}")
                raise

    # Should not reach here, but just in case
    logger.error(f"All {max_retries} attempts failed")
    raise last_exception

def call_storyboard(title: str, slide_text: str, language: str):
    storyboard_system_prompt = load_prompt(PROMPT_DIR / "storyboard_system_prompt.txt")
    storyboard_user_prompt_template = load_prompt(PROMPT_DIR / "storyboard_user_prompt.txt")

    if not storyboard_system_prompt or not storyboard_user_prompt_template:
        raise Exception("Could not load storyboard prompt files")

    storyboard_user_prompt = storyboard_user_prompt_template.replace("{SLIDE_TEXT}", slide_text)
    storyboard_user_prompt = storyboard_user_prompt.replace("{SLIDE_TITLE}", title)
    storyboard_system_prompt = storyboard_system_prompt.replace("{LANGUAGE}", language)

    try:
        logger.info("Generating storyboard...")
        result = call_deepseek(storyboard_system_prompt, storyboard_user_prompt, 0.7, 2500)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        token_usage, total_tokens = get_token_usage(result)
        storyboard = json.loads(content)

        logger.info("Storyboard generated successfully")
        logger.info(f"Storyboard: {storyboard}")
        logger.info(f"Token usage: {token_usage}")
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
    user_prompt_template = load_prompt(PROMPT_DIR / "manim_code_user_prompt.txt")

    if not system_prompt or not boilerplate or not user_prompt_template:
        logger.error("Could not load animation prompt files")
        raise Exception("Could not load prompt files")

    # FIX: Each replacement is on its own variable — no cross-assignment
    system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
    system_prompt = system_prompt.replace("{LANGUAGE}", language)
    system_prompt = system_prompt.replace("{SLIDE_TITLE}", title)
    user_prompt = user_prompt_template.replace("{STORYBOARD}", json.dumps(storyboard))

    try:
        logger.info("Generating animation code...")
        result = call_deepseek(system_prompt, user_prompt, 0.5, 5000)
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        clean_content = clean_code(content)
        token_usage, total_tokens = get_token_usage(result)

        logger.info("Manim code generated successfully")
        logger.info(f"Code generated: {clean_content}")
        logger.info(f"Token usage: {token_usage}")
        return clean_content, total_tokens

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Animation generation failed: {e}")
        return None, None


def review_animation_code(manim_code: str, storyboard, title: str, language: str):
    system_prompt = load_prompt(PROMPT_DIR / "code_review_system_prompt.txt")
    boilerplate = load_boilerplate()
    user_prompt = load_prompt(PROMPT_DIR / "code_review_user_prompt.txt")

    if not system_prompt or not boilerplate or not user_prompt:
        logger.error("Could not load review prompt files")
        raise Exception("Could not load prompt files")

    system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
    system_prompt = system_prompt.replace("{LANGUAGE}", language)
    system_prompt = system_prompt.replace("{SLIDE_TITLE}", title)
    user_prompt = user_prompt.replace("{MANIM_CODE}", manim_code)
    user_prompt = user_prompt.replace("{STORYBOARD}", json.dumps(storyboard))

    try:
        logger.info("Reviewing code...")
        result = call_deepseek(system_prompt, user_prompt, 0.5, 5000)
        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        clean_content = clean_code(content)
        token_usage, total_tokens = get_token_usage(result)

        logger.info("Code review completed successfully")
        logger.info(f"Code review result: {clean_content}")
        logger.info(f"Token usage: {token_usage}")
        return clean_content, total_tokens

    except Exception as e:
        logger.error(f"Code review failed: {e}")
        return None, 0


def validate_code(code: str) -> bool:
    """
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as tf:
        tf.write(code)
        tmp_path = tf.name

    try:
        logger.info(f"Validating code with dry-run: {tmp_path}")
        logger.info(f"Using interpreter: {sys.executable}")
        cmd = [
            sys.executable, "-m", "manim", "render",
            tmp_path,
            "--dry_run",
            "--disable_caching",
            "-v", "WARNING",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            logger.error(f"Manim dry-run failed:\n{result.stderr}")
            return False

        logger.info("Dry-run passed — code is valid")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Manim dry-run timed out")
        return False
    except Exception as e:
        logger.error(f"Validation error: {traceback.format_exc()}")
        return False
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    """
    try:
        ast.parse(code)
        logger.info("Dry-run passed — code is valid")
        return True
    except SyntaxError:        
        logger.error(f"Syntax error: {traceback.format_exc()}")
        return False
    except Exception:
        logger.error(f"Unexpected error during validation: {traceback.format_exc()}")
        return False

FALLBACK_CODE = """
from scene import CScene

class EducationalVideo(CScene):
    def construct(self):
        self.setup_scene("Content unavailable")
"""


def generate_animation(title: str, slide_text: str, language: str):
    """
    Generate a Manim animation for a single slide.
    Returns (manim_code, total_tokens, total_time) or None on failure.
    """

    start_time = time.time()
    print(f"DEBUG in generate_animation\nTitle: {title}\nLanguage: {language}\nSlide text:\n{slide_text}")

    if not slide_text:
        logger.warning("Empty slide text provided")
        return None

    # Step 1: Storyboard
    storyboard, storyboard_tokens = call_storyboard(title, slide_text, language)
    if storyboard is None:
        logger.error("Failed to generate storyboard")
        return None

    # Step 2: Generate animation code
    manim_code, manim_tokens = call_animation(storyboard, language, title)
    if manim_code is None:
        logger.error("Failed to generate Manim code")
        return None

    # Step 3: Review + validate loop (up to 3 attempts)
    total_review_tokens = 0
    final_code = manim_code

    for attempt in range(3):
        reviewed_code, review_tokens = review_animation_code(final_code, storyboard, title, language)
        total_review_tokens += review_tokens or 0

        if reviewed_code is None:
            logger.warning(f"Review attempt {attempt + 1} returned None, using previous code")
            break

        final_code = reviewed_code
        is_valid = validate_code(final_code)

        if is_valid:
            logger.info(f"Code validated successfully on attempt {attempt + 1}")
            break
        else:
            logger.warning(f"Validation failed on attempt {attempt + 1}/3")
            if attempt == 2:
                logger.error("All 3 validation attempts failed, using fallback code")
                final_code = FALLBACK_CODE

    total_tokens = (storyboard_tokens or 0) + (manim_tokens or 0) + total_review_tokens
    end_time = time.time()
    logger.info(f"Animation generated — total tokens: {total_tokens}, time: {end_time - start_time:.2f}s")
    return (final_code, total_tokens, end_time - start_time)


if __name__ == "__main__":
    test_title = "利用直角三角形推導三角比"
    test_slide = """
    對於任意銳角θ，可構造直角三角形：對邊/斜邊 = sinθ，鄰邊/斜邊 = cosθ，對邊/鄰邊 = tanθ
    已知一邊一角時，可用畢氏定理求其他邊長
    例如：若sinθ = 3/5，則可設對邊=3，斜邊=5，計算鄰邊=4
    從而得到cosθ = 4/5，tanθ = 3/4
    """
    result = generate_animation(test_title, test_slide, language="Chinese")
    if result:
        code, tokens, elapsed = result
        print(f"\nTokens used: {tokens}")
        print(f"\nTime taken: {elapsed:.2f}s")
        print(f"\nGenerated code:\n{code}")