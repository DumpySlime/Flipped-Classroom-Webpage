from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from bson import ObjectId
from datetime import datetime

import requests
import subprocess
import tempfile
import os
import shutil
import re
import sys


video_gen_bp = Blueprint("video_generation", __name__)

db = None
DEEPSEEK_API_KEY = None
DEEPSEEK_MODEL = None
DEEPSEEK_BASE_URL = None

def get_manim_command():
    """
    Return the Manim command as a list, portable across macOS and Windows.
    - On macOS: try Homebrew path first, then fall back to 'manim' on PATH.
    - On Windows/Linux: use 'manim' and rely on PATH.
    """
    if sys.platform == "darwin":
        homebrew_path = "/opt/homebrew/bin/manim"
        if os.path.exists(homebrew_path):
            return [homebrew_path]
        return ["manim"]
    else:
        # Windows and Linux
        return ["manim"]



def init_video_generation(database, app):
    """Initialize video generation module with DB and app config."""
    global db, DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
    db = database
    DEEPSEEK_API_KEY = app.config.get("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL = app.config.get("DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL = app.config.get("DEEPSEEK_BASE_URL")

    print("[VIDEO_GEN] Video generation module initialized")
    print(f"[VIDEO_GEN] DeepSeek model: {DEEPSEEK_MODEL}")


# ---------- Helpers for slide extraction ----------


def extract_title(slide_content: str) -> str:
    """Get a reasonable title from slide text."""
    for line in slide_content.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Markdown-style heading
        if line.startswith("#"):
            return line.lstrip("#").strip()
        # Otherwise first short line
        if len(line) < 80:
            return line
    return "Untitled Slide"


def extract_slides(content: str):
    """Split material content into slides."""
    if not content:
        return []

    if "---" in content:
        parts = content.split("---")
    elif "\n\n\n" in content:
        parts = content.split("\n\n\n")
    else:
        parts = [content]

    slides = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue

        slides.append({
            "slide_number": i + 1,
            "title": extract_title(part),
            "content": part,
        })

    return slides


# ---------- 1) Prepare: get material + slides ----------


@video_gen_bp.route("/api/generate-video/prepare", methods=["POST"])
@jwt_required()
def prepare_video_generation():
    """Extract slide content and prepare for Manim generation."""
    try:
        if db is None:
            return jsonify({"error": "Database not initialized"}), 500

        data = request.get_json() or {}
        material_id_str = data.get("material_id")

        if not material_id_str:
            return jsonify({"error": "material_id is required"}), 400

        try:
            material_obj_id = ObjectId(material_id_str)
        except Exception:
            return jsonify({"error": "Invalid material_id format"}), 400

        material = db.materials.find_one({"_id": material_obj_id})
        if not material:
            return jsonify({"error": "Material not found"}), 404

        raw_slides = material.get("slides", [])
        if not raw_slides:
            return jsonify({"error": "No slides found in this material"}), 400

        topic = material.get("topic") or material.get("title") or "Educational Topic"

        slides = []
        for idx, s in enumerate(raw_slides, start=1):
            # Case 1: slide is an object like in your snippet
            if isinstance(s, dict):
                subtitle = s.get("subtitle", f"Slide {idx}")
                contents = s.get("content", [])
                if isinstance(contents, list):
                    content_text = "\n".join(str(c) for c in contents)
                else:
                    content_text = str(contents)
                page = s.get("page", idx)
            # Case 2: slide is already a plain string
            else:
                subtitle = f"Slide {idx}"
                content_text = str(s)
                page = idx

            slides.append({
                "slide_number": page,
                "title": subtitle,
                "content": content_text,
            })

        return jsonify(
            {
                "material_id": material_id_str,
                "topic": topic,
                "slides": slides,
                "total_slides": len(slides),
            }
        ), 200

    except Exception as e:
        print("[VIDEO_GEN] Error in prepare_video_generation:", str(e))
        return jsonify(
            {"error": "Failed to prepare video generation", "details": str(e)}
        ), 500



MANIM_STORYBOARD_SYSTEM_PROMPT = """You are an expert educational animator specializing in creating Manim storyboards.

Given slide content, generate a detailed scene-by-scene storyboard for a Manim animation.

For each scene, describe:
1. Visual elements (text, shapes, equations, diagrams)
2. Animation types (Write, FadeIn, Transform, etc.)
3. Timing and transitions
4. Camera movements (if needed)
5. Colors and styling

Output format:

Scene 1: [Title]
Duration: [X seconds]
Visual:
- [element description]
Animations:
- [animation description with order + timing]

Scene 2: ...

Keep descriptions clear, concise, and implementable in Manim.
Do NOT output any code, only natural language storyboard.
""".strip()


def create_storyboard_prompt(slides, topic: str) -> str:
    slide_text = "\n\n".join(
        f"Slide {s['slide_number']}: {s['title']}\n{s['content']}" for s in slides
    )
    return f"""
Create a Manim animation storyboard for an educational video on "{topic}".

Slides:
{slide_text}

Follow the requested storyboard format (Scene 1, Scene 2, ...).
""".strip()


@video_gen_bp.route("/api/generate-video/storyboard", methods=["POST"])
@jwt_required()
def generate_manim_storyboard():
    """Generate storyboard using DeepSeek."""
    try:
        if not DEEPSEEK_API_KEY or not DEEPSEEK_MODEL or not DEEPSEEK_BASE_URL:
            return jsonify({"error": "DeepSeek is not configured"}), 500

        data = request.get_json() or {}
        slides = data.get("slides") or []
        topic = data.get("topic", "Educational Topic")

        if not slides:
            return jsonify({"error": "slides array is required"}), 400

        user_prompt = create_storyboard_prompt(slides, topic)

        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": MANIM_STORYBOARD_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.7,
            },
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=90,
        )
        resp.raise_for_status()
        data_json = resp.json()
        storyboard = data_json["choices"][0]["message"]["content"].strip()

        return jsonify({"topic": topic, "storyboard": storyboard}), 200

    except Exception as e:
        print("[VIDEO_GEN] Error generating storyboard:", str(e))
        return jsonify({"error": "Failed to generate storyboard", "details": str(e)}), 500

MANIM_STORYBOARD_SYSTEM_PROMPT = """
You are an expert educational animator specializing in creating Manim storyboards.

Given slide content, generate a detailed scene-by-scene storyboard for a Manim animation.

Structure the video into at least 4 scenes:
1) Introduction to the topic
2) Key concepts explained
3) Worked example or visualization
4) Summary / recap

Target total duration: 60–120 seconds.

For each scene, describe:
- Visual elements (text, shapes, equations, diagrams)
- Animation types (Write, FadeIn, Transform, etc.)
- Timing and transitions with approximate seconds
- Camera movements (if needed)
- Colors and styling

Output format:

Scene 1: [Title]
Duration: [X seconds]
Visual:
- [element description]
Animations:
- [animation description with order + timing]

Scene 2: ...
Scene 3: ...
Scene 4: ...

Keep descriptions clear, concise, and implementable in Manim.
Do NOT output any code, only natural language storyboard.
""".strip()

MANIM_CODE_SYSTEM_PROMPT = """
You are an expert Manim programmer. Generate complete, executable Manim Community Edition v0.18+ code for an educational video.

from manim import *
class CreateCircle(Scene):
    def construct(self):
        circle = Circle()  # create a circle
        circle.set_fill(PINK, opacity=0.5)  # set the color and transparency
        self.play(Create(circle))  # show the circle on screen

Requirements:
- from manim import *
- Define class EducationalVideo(Scene):
- Implement the storyboard exactly: match scenes, visuals, animations (Write, FadeIn, Transform, etc.) and timing.
- Use smooth transitions (self.wait(1), etc.).
- Colors: BLUE for titles, GREEN for equations, standard Manim styling.
- Total runtime 60–120 seconds.
- No extra narration/audio; focus on visuals.
- Code must run with:
  - python file.py
  - manim -qm file.py EducationalVideo

Syntax and indentation rules:
- The Python code must be syntactically valid: no unmatched parentheses and no incorrect indentation.
- Use valid Python 3.12 syntax with 4-space indentation.
- Do NOT start a line with extra indentation unless it is inside a class or function body.
- Do NOT leave lines like `triangle.animate.set_color(YELLOW),` by themselves; they must be part of self.play(...) or removed.
- Do NOT leave trailing commas or standalone expressions (e.g. an animation call followed by just a comma).
- The code must compile without SyntaxError when checked with: compile(code, "<generated-manim>", "exec").

- Every self.play(...) call must be on a single line with matching parentheses.
- Never split a self.play( call across multiple lines unless you use explicit line continuation with matching brackets.

- Total runtime must be between 55 and 65 seconds.
- Use at least 10–15 self.play(...) calls in construct().
- Every self.play(...) must have an explicit run_time between 2 and 4 seconds.
- After each main scene, call self.wait(1.0) or self.wait(1.5) so the viewer can read.
- Do NOT end the scene early: play through all scenes from the storyboard to reach about 60 seconds total.

- Use at least 20 self.play(...) calls.
- Every self.play(...) must include run_time between 2.0 and 4.0 seconds (no smaller values).
- Do NOT use run_time less than 2.0.

- Do NOT use MathTex or Tex anywhere.
- For all formulas/equations, use Text(...) with plain characters instead of LaTeX
  (for example: Text("sin(theta) = opposite / hypotenuse")).


Output ONLY the Python code, no explanations.
""".strip()



def create_code_generation_prompt(storyboard: str, topic: str) -> str:
    return f"""
Topic: {topic}

Storyboard:
{storyboard}

Generate the Manim code following the requirements.
""".strip()


def extract_code_block(text: str) -> str:
    """Extract python code from ```python ... ``` or return raw text."""
    m = re.search(r"```python(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"```(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


@video_gen_bp.route("/api/generate-video/code", methods=["POST"])
@jwt_required()
def generate_manim_code():
    """Generate executable Manim code from storyboard."""
    try:
        if not DEEPSEEK_API_KEY or not DEEPSEEK_MODEL or not DEEPSEEK_BASE_URL:
            return jsonify({"error": "DeepSeek is not configured"}), 500

        data = request.get_json() or {}
        storyboard = data.get("storyboard", "")
        topic = data.get("topic", "Educational Video")

        if not storyboard:
            return jsonify({"error": "storyboard is required"}), 400

        user_prompt = create_code_generation_prompt(storyboard, topic)

        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": MANIM_CODE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.5,
            },
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )

        resp.raise_for_status()
        data_json = resp.json()

        choices = data_json.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return jsonify({"error": "DeepSeek returned no choices"}), 500

        first = choices[0]
        message = first.get("message", {})
        raw = message.get("content", "")

        manim_code = extract_code_block(raw)
        
        manim_code = (
            manim_code.replace("```python", "")
            .replace("```", "")
            .strip()
        )
        return jsonify({"topic": topic, "manim_code": manim_code}), 200

    except Exception as e:
        print("[VIDEO_GEN] Error generating Manim code:", str(e))
        return jsonify({"error": "Failed to generate Manim code", "details": str(e)}), 500

def find_video_file(rootdir: str, materialid: str) -> str | None:
    """
    Try to get the full Manim render, not the short scene previews.

    1. Prefer the expected output filename we asked Manim to create.
    2. If that does not exist, fall back to the largest .mp4 in the folder.
    """
    # 1) Expected filename from the manim command: video<materialid>.mp4
    expected_name = f"video_{materialid}.mp4"
    expected_path = os.path.join(rootdir, expected_name)
    if os.path.exists(expected_path):
        return expected_path

    # 2) Fallback: choose the largest .mp4 (full render is usually the biggest)
    candidates = []
    for root, _, files in os.walk(rootdir):
        for f in files:
            if f.lower().endswith(".mp4"):
                path = os.path.join(root, f)
                size = os.path.getsize(path)
                candidates.append((size, path))

    if candidates:
        # return the path of the largest file
        return max(candidates, key=lambda x: x[0])[1]

    return None



def _save_video_to_static(video_path: str, material_id_str: str) -> str:
    out_dir = os.path.join("static", "generated_videos")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, f"video_{material_id_str}.mp4")
    shutil.copy(video_path, dest)
    return f"/static/generated_videos/video_{material_id_str}.mp4"


@video_gen_bp.route("/api/generate-video/render", methods=["POST"])
@jwt_required()
def render_manim_video():
    """Render Manim code into video and store URL on material."""
    script_path = None 
    try:
        if db is None:
            return jsonify({"error": "Database not initialized"}), 500

        data = request.get_json() or {}
        manim_code = data.get("manim_code", "")
        material_id_str = data.get("material_id")
        quality = data.get("quality", "medium")

        if not manim_code:
            return jsonify({"error": "manim_code is required"}), 400
        if not material_id_str:
            return jsonify({"error": "material_id is required"}), 400

        try:
            material_obj_id = ObjectId(material_id_str)
        except Exception:
            return jsonify({"error": "Invalid material_id format"}), 400

        unsafe_code = manim_code or ""

        # 1) Strip fences and bad chars
        safe_code = unsafe_code.replace("```python", "").replace("```", "")
        safe_code = re.sub(r"\ufffd.", "", safe_code, flags=re.IGNORECASE)
        safe_code = safe_code.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        safe_code = safe_code.replace("MathTex(", "Text(")


        # 2) Normalize indentation
        lines = safe_code.splitlines()
        normalized = []
        for line in lines:
            line = line.replace("\t", "    ") 
            normalized.append(line.rstrip())
        safe_code = "\n".join(normalized).lstrip() 
        
        safe_code = re.sub(
            r".*RightAngle\([^)]*\)\s*\n",
            "",
            safe_code,
        )

        # 3) Syntax check
        try:
            compile(safe_code, "<generated-manim>", "exec")
        except SyntaxError as e:
            return jsonify(
                {
                    "error": "Generated Manim code has a syntax error",
                    "details": f"{e.__class__.__name__}: {e}",
                }
            ), 400

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(safe_code)
            script_path = f.name
        print("[VIDEO_GEN] script_path:", script_path)

        quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}.get(
            quality, "-qm"
        )
        out_dir = tempfile.mkdtemp()
        print("[VIDEO_GEN] Manim temp dir:", out_dir)
        
        videopath = None

        try:
            print(f"[VIDEO_GEN] Rendering Manim video for {material_id_str}...")

            cmd = get_manim_command() + [
                quality_flag,
                script_path,
                "EducationalVideo",
                "-o",
                f"video_{material_id_str}",
            ]

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=out_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=600,
                )
                print("MANIM STDOUT:\n", proc.stdout)
                print("MANIM STDERR:\n", proc.stderr)
            except Exception as sub_err:
                return (
                    jsonify(
                        {
                            "error": "Failed to start Manim subprocess",
                            "details": str(sub_err),
                        }
                    ),
                    500,
                )


            if proc.returncode != 0:
                # Try to locate a rendered video anyway
                maybe_video = find_video_file(out_dir, material_id_str)
                if maybe_video:
                    # Treat as success if an mp4 was produced
                    videopath = maybe_video
                else:
                    out_text = (proc.stdout or "").strip()
                    err_text = (proc.stderr or "").strip()
                    combined = (out_text + "\n\n" + err_text).strip()
                    return (
                        jsonify(
                            {
                                "error": "Manim rendering failed",
                                "details": combined[:4000],
                            }
                        ),
                        500,
                    )
            else:
                videopath = find_video_file(out_dir, material_id_str)
                if not videopath:
                    all_videos = []
                    for root, _, files in os.walk(out_dir):
                        for f in files:
                            if f.lower().endswith(".mp4"):
                                all_videos.append(os.path.join(root, f))
                    print("VIDEOGEN: No suitable video found. MP4 files:", all_videos)
                    return jsonify(error="Rendered video not found"), 500

            video_url = _save_video_to_static(videopath, material_id_str)

            db.materials.update_one(
                {"_id": material_obj_id},
                {
                    "$set": {
                        "video_url": video_url,
                        "video_generated_at": datetime.utcnow(),
                    }
                },
            )

            return (
                jsonify(
                    {
                        "success": True,
                        "video_url": video_url,
                        "message": "Video generated",
                    }
                ),
                200,
            )

        finally:
            if script_path and os.path.exists(script_path):
                os.unlink(script_path)

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video rendering timed out"}), 408

    except Exception as e:
        return jsonify(
            {
                "error": "Failed to render video",
                "details": str(e),
            }
        ), 500

