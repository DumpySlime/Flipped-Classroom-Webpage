# Testing storyboard and scene rendering
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL")

def get_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504, 429)):
    """Custom retry logic for API calls."""
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
            return f.read().strip()
    except FileNotFoundError:
        print(f"Warning: Prompt file not found: {prompt_file}")
        return None

def call_deepseek_storyboard(slide_text):
    """Call DeepSeek to generate storyboard JSON."""
    if not DEEPSEEK_API_KEY:
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")

    # Load prompts
    base_dir = Path(__file__).parent / "prompt"
    system_prompt = load_prompt(base_dir / "storyboard_system_prompt.txt")
    user_prompt_template = load_prompt(base_dir / "storyboard_user_prompt.txt")

    if not system_prompt or not user_prompt_template:
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

        print("=" * 60)
        print("CALLING DEEPSEEK API FOR STORYBOARD")
        print("=" * 60)
        print(f"Slide text: {slide_text}...")
        print()

        response = session.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON
        storyboard = json.loads(content)

        print("STORYBOARD GENERATED SUCCESSFULLY:")
        print(json.dumps(storyboard, indent=2))
        print()

        return storyboard

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw response: {content}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise


def call_deepseek_manim_code(storyboard):
    """Call DeepSeek to generate Manim code from storyboard."""
    if not DEEPSEEK_API_KEY:
        raise Exception("DEEPSEEK_API_KEY environment variable is not set")

    # Load prompts
    base_dir = Path(__file__).parent / "prompt"
    system_prompt = load_prompt(base_dir / "manim_code_system_prompt.txt")
    boilerplate = load_prompt(base_dir / "boilerplate_api_doc.txt")

    if not system_prompt:
        raise Exception("Could not load manim_code_system_prompt.txt")

    # Format system prompt with boilerplate
    if boilerplate:
        system_prompt = system_prompt.replace("{boilerplate_api_doc.txt}", boilerplate)

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

        print("=" * 60)
        print("CALLING DEEPSEEK API FOR MANIM CODE")
        print("=" * 60)
        print()

        response = session.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        print("MANIM CODE GENERATED SUCCESSFULLY:")
        print(content)
        print()

        return content

    except Exception as e:
        print(f"Error: {e}")
        raise


def test_storyboard_generation():
    """Test storyboard generation with sample slide."""
    test_slide = """
        A polygon is a closed shape with straight sides
        All sides connect end-to-end to form a single closed path
        Polygons are named by how many sides they have
    """

    try:
        storyboard = call_deepseek_storyboard(test_slide)
        return storyboard
    except Exception as e:
        print(f"Storyboard generation failed: {e}")
        return None


def test_manim_code_generation(storyboard):
    """Test Manim code generation from storyboard."""
    try:
        manim_code = call_deepseek_manim_code(storyboard)
        return manim_code
    except Exception as e:
        print(f"Manim code generation failed: {e}")
        return None

if __name__ == "__main__":
    print("Testing DeepSeek Prompt Integration")
    print("=" * 60)
    print()

    # Check API key
    if not DEEPSEEK_API_KEY:
        print("ERROR: DEEPSEEK_API_KEY not set in environment variables")
        print("Please set it in your .env file or system environment")
        sys.exit(1)

    print("✓ DeepSeek API Key loaded")
    print()

    # Test 1: Storyboard Generation
    print("TEST 1: Storyboard Generation")
    print("-" * 60)
    storyboard = test_storyboard_generation()

    if storyboard:
        print("✓ Storyboard generation successful")
        print()

        # Test 2: Manim Code Generation
        print("TEST 2: Manim Code Generation")
        print("-" * 60)
        manim_code = test_manim_code_generation(storyboard)

        if manim_code:
            print("✓ Manim code generation successful")
        else:
            print("✗ Manim code generation failed")
    else:
        print("✗ Storyboard generation failed")

    print()
    print("=" * 60)
    print("Testing Complete")    