# Testing storyboard and scene rendering
import sys
import os
import json
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

def setup_logging(log_file="logs/test.log", log_level=logging.INFO):
    """Configure logging with both file and console handlers."""
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

def get_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504, 429)):
    """Custom retry logic for API calls."""
    logger.debug(f"Creating session with {retries} retries and {backoff_factor} backoff factor")
    session = requests.Session()
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

def load_prompt(prompt_file):
    """Load prompt from file."""
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            logger.debug(f"Successfully loaded prompt from: {prompt_file}")
            return content
    except FileNotFoundError:
        logger.warning(f"Prompt file not found: {prompt_file}")
        return None
    except Exception as e:
        logger.error(f"Error loading prompt file {prompt_file}: {e}")
        return None

def parse_token_usage(result):
    """Parse and return token usage from API response."""
    usage = result.get("usage", {})
    return {
        "prompt": usage.get("prompt_tokens", 0),
        "completion": usage.get("completion_tokens", 0),
        "total": usage.get("total_tokens", 0)
    }

def print_token_usage(token_usage, stage_name):
    """Print formatted token usage."""
    logger.info(f"{stage_name} Token Usage:")
    logger.info(f"  Prompt:     {token_usage['prompt']:,}")
    logger.info(f"  Completion: {token_usage['completion']:,}") 
    logger.info(f"  Total:      {token_usage['total']:,}")
    return token_usage

def call_deepseek_storyboard(slide_text):
    """Call DeepSeek to generate storyboard JSON."""
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY environment variable is not set")
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")

    # Load prompts
    base_dir = Path(__file__).parent / "prompt"
    system_prompt = load_prompt(base_dir / "storyboard_system_prompt.txt")
    user_prompt_template = load_prompt(base_dir / "storyboard_user_prompt.txt")

    if not system_prompt or not user_prompt_template:
        logger.error("Could not load required prompt files")
        raise Exception("Could not load prompt files")

    # Format user prompt with slide text
    user_prompt = user_prompt_template.replace("{SLIDE_TEXT}", slide_text)

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
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}
        }

        logger.info("=" * 60)
        logger.info("CALLING DEEPSEEK API FOR STORYBOARD")
        logger.info("=" * 60)
        logger.info(f"Slide text: {slide_text}")
        logger.debug(f"Full slide text: {slide_text}")

        response = session.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        token_usage = parse_token_usage(result)
        print_token_usage(token_usage, "STORYBOARD")

        # Parse JSON
        storyboard = json.loads(content)

        logger.info("STORYBOARD GENERATED SUCCESSFULLY")
        logger.debug(f"Storyboard content: {json.dumps(storyboard, indent=2)}")
        logger.debug(f"Token usage: {token_usage}")

        return storyboard, token_usage

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        logger.error(f"Raw response content: {content}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in storyboard generation: {e}", exc_info=True)
        raise


def call_deepseek_manim_code(storyboard):
    """Call DeepSeek to generate Manim code from storyboard."""
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY environment variable is not set")
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")

    # Load prompts
    base_dir = Path(__file__).parent / "prompt"
    system_prompt = load_prompt(base_dir / "manim_code_system_prompt.txt")
    boilerplate = load_prompt(base_dir / "boilerplate_api_doc.txt")

    if not system_prompt:
        logger.error("Could not load manim_code_system_prompt.txt")
        raise Exception("Could not load manim_code_system_prompt.txt")

    # Format system prompt with boilerplate
    if boilerplate:
        system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)
        logger.debug("Boilerplate documentation included in system prompt")

    user_prompt = f"Generate Manim code for this storyboard:\n\n{json.dumps(storyboard, indent=2)}"

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
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 5000
        }

        logger.info("=" * 60)
        logger.info("CALLING DEEPSEEK API FOR MANIM CODE")
        logger.info("=" * 60)

        response = session.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        token_usage = parse_token_usage(result)

        logger.info("MANIM CODE GENERATED SUCCESSFULLY")
        logger.debug(f"Generated Manim code:\n{content}")
        print_token_usage(token_usage, "MANIM CODE")

        return content, token_usage

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Manim code generation: {e}", exc_info=True)
        raise

def validate_code(storyboard, manim_code, boilerplate):
    """Full pipeline validation."""
    review_prompt = load_prompt("prompt/code_review_prompt.txt")
    
    full_context = review_prompt.format(
        boilerplate_api_doc_txt=boilerplate,
        storyboard_json=json.dumps(storyboard, indent=2),
        generated_code=manim_code
    )
    
    response = call_deepseek({
        "messages": [{"role": "system", "content": full_context}],
        "temperature": 0.1
    })
    
    review = json.loads(response["choices"][0]["message"]["content"])
    
    if review["status"] == "PASS":
        return manim_code  # Ready to render
    else:
        logger.warning(f"Code review failed: {review['total_issues']} issues")
        return review["fixed_code"]  # Use auto-fixed version

def test_storyboard_generation():
    """Test storyboard generation with sample slide."""
    test_slide = """
        Every right triangle has one 90° angle
        The longest side is called the hypotenuse (opposite the right angle)
        The other two sides are adjacent (next to) and opposite (across from) the angle we're studying
    """

    logger.info("Starting storyboard generation test")
    try:
        storyboard, storyboard_token = call_deepseek_storyboard(test_slide)
        logger.info("Storyboard generation test completed successfully")
        return storyboard, storyboard_token
    except Exception as e:
        logger.error(f"Storyboard generation test failed: {e}")
        return None


def test_manim_code_generation(storyboard):
    """Test Manim code generation from storyboard."""
    logger.info("Starting Manim code generation test")
    try:
        manim_code, manim_code_token = call_deepseek_manim_code(storyboard)
        logger.info("Manim code generation test completed successfully")
        return manim_code, manim_code_token
    except Exception as e:
        logger.error(f"Manim code generation test failed: {e}")
        return None

if __name__ == "__main__":
    logger.info("Starting test script")
    print("Testing DeepSeek Prompt Integration")
    print("=" * 60)
    print()

    # Check API key
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY not set in environment variables")
        print("ERROR: DEEPSEEK_API_KEY not set in environment variables")
        print("Please set it in your .env file or system environment")
        sys.exit(1)

    logger.info("DEEPSEEK_API_KEY loaded successfully")
    print("✓ DeepSeek API Key loaded")
    print()

    total_tokens = {"prompt": 0, "completion": 0, "total": 0}

    # Test 1: Storyboard Generation
    print("TEST 1: Storyboard Generation")
    print("-" * 60)
    storyboard, storyboard_token = test_storyboard_generation()

    if storyboard:
        logger.info("TEST 1 PASSED: Storyboard generation successful")
        logger.info(f"Generated storyboard:\n{json.dumps(storyboard, indent=2)}")
        print("✓ Storyboard generation successful")
        total_tokens["prompt"] += storyboard_token["prompt"]
        total_tokens["completion"] += storyboard_token["completion"]
        total_tokens["total"] += storyboard_token["total"]
        print()

        # Test 2: Manim Code Generation
        print("TEST 2: Manim Code Generation")
        print("-" * 60)
        manim_code, manim_code_token = test_manim_code_generation(storyboard)

        if manim_code:
            logger.info("TEST 2 PASSED: Manim code generation successful")
            logger.info(f"Generated Manim code:\n{manim_code}")
            total_tokens["prompt"] += manim_code_token["prompt"]
            total_tokens["completion"] += manim_code_token["completion"]
            total_tokens["total"] += manim_code_token["total"]
            print("✓ Manim code generation successful")
        else:
            logger.warning("TEST 2 FAILED: Manim code generation failed")
            print("✗ Manim code generation failed")
    else:
        logger.warning("TEST 1 FAILED: Storyboard generation failed")
        print("✗ Storyboard generation failed")

    print()
    print("=" * 60)
    print("TOTAL TOKEN USAGE:")
    print(f"  Prompt:     {total_tokens['prompt']:,}")
    print(f"  Completion: {total_tokens['completion']:,}")
    print(f"  Grand Total: {total_tokens['total']:,}")
    print("Testing Complete")
    logger.info("Test script completed")