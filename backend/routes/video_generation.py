from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from bson import ObjectId
from datetime import datetime
import subprocess
import tempfile
import os
import shutil
import re
import sys
from pathlib import Path
from utils.manim.generate_animation import generate_animation

video_gen_bp = Blueprint("video_generation", __name__)

db = None

BASE_DIR = Path(__file__).resolve().parent.parent
MANIM_DIR = BASE_DIR / "utils" / "manim"
SCENE_PATH = MANIM_DIR / "scene.py"


def init_video_generation(database, app):
    """Initialize video generation module with DB."""
    global db
    db = database
    print("VIDEOGEN: Video generation module initialized")


def get_manim_command() -> str:
    """Return the Manim command, preferring Homebrew on macOS."""
    if sys.platform == "darwin":
        homebrew_path = "/opt/homebrew/bin/manim"
        if os.path.exists(homebrew_path):
            return homebrew_path
    return "manim"


def find_video_file(root_dir: str, material_id: str) -> str | None:
    expected_name = f"video_{material_id}.mp4"
    expected_path = os.path.join(root_dir, expected_name)
    if os.path.exists(expected_path):
        return expected_path

    candidates = []
    for root, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".mp4"):
                full = os.path.join(root, f)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                candidates.append((size, full))

    return max(candidates, key=lambda x: x[0])[1] if candidates else None


def save_video_to_static(video_path: str, material_id_str: str) -> str:
    out_dir = os.path.join("static", "generated_videos")
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, f"video_{material_id_str}.mp4")
    shutil.copy(video_path, dest)
    return f"static/generated_videos/video_{material_id_str}.mp4"


def extract_slides_from_material(material: dict) -> list[dict]:
    """
    Extract slides from a material document.
    Supports:
      - material["slides"] as a list[dict]
      - material["slides"] as {"slides": list[dict]}  # older shape
    Skips first & last when there are ≥3 slides, else uses all.
    """
    raw = material.get("slides", [])

    # Handle nested shape: {"slides": [ ... ]}
    if isinstance(raw, dict) and "slides" in raw:
        raw_slides = raw.get("slides") or []
    elif isinstance(raw, list):
        raw_slides = raw
    else:
        raw_slides = []

    all_slides: list[dict] = []

    for idx, s in enumerate(raw_slides, start=1):
        if isinstance(s, dict):
            subtitle = s.get("subtitle", f"Slide {idx}")
            contents = s.get("content", "")
            if isinstance(contents, list):
                content_text = " ".join(str(c) for c in contents)
            else:
                content_text = str(contents)
        else:
            subtitle = f"Slide {idx}"
            content_text = str(s)

        all_slides.append({"title": subtitle, "content": content_text})

    n = len(all_slides)
    if n >= 3:
        # skip first (intro) and last (conclusion)
        return all_slides[1:-1]
    return all_slides



@video_gen_bp.route("/api/generate-video/generate", methods=["POST"])
# @jwt_required()
def generate_video():
    """
    Extract slides from material (ignoring first & last when possible),
    pass slide text to generate_animation(), then render the returned
    Manim code into a video.
    """
    script_path = None
    out_dir = None

    try:
        if db is None:
            return jsonify({"error": "Database not initialized"}), 500

        data = request.get_json(silent=True) or {}
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

        raw_slides = material.get("slides", []) or []
        if not raw_slides:
            return jsonify({"error": "No slides found in this material"}), 400

        slides = extract_slides_from_material(material)
        print(
            "DEBUG slides count after filtering:",
            len(slides),
            "raw slides:",
            len(raw_slides),
        )
        if not slides:
            return jsonify({"error": "Slides could not be extracted"}), 400

        # Build a single slide_text string to pass to generate_animation
        topic = material.get("topic") or material.get("title") or "Educational Topic"
        slide_text = f"Topic: {topic}\n\n" + "\n".join(
            f"{s['title']}\n{s['content']}" for s in slides
        )
        # More useful debug (length + prefix, not the whole thing)
        print("DEBUG slide_text length:", len(slide_text))
        print("DEBUG slide_text first 500 chars:\n", slide_text[:500])

        # generate_animation handles prompts + DeepSeek calls
        manim_code = generate_animation(slide_text)
        if not manim_code:
            return jsonify({"error": "Failed to generate animation code"}), 500

        # Sanitize code before rendering
        safe_code = manim_code
        safe_code = re.sub(r"```.*?```", "", safe_code, flags=re.IGNORECASE)
        safe_code = safe_code.encode("utf-8", errors="replace").decode(
            "utf-8", errors="replace"
        )
        safe_code = safe_code.replace("MathTex", "Text")
        safe_code = "\n".join(line.rstrip() for line in safe_code.splitlines()).lstrip()
        safe_code = re.sub(r"\.RightAngle", "", safe_code)

        # Compile check
        try:
            compile(safe_code, "generated-manim", "exec")
        except SyntaxError as e:
            return (
                jsonify(
                    {
                        "error": "Generated Manim code has a syntax error",
                        "details": f"{e.__class__.__name__}: {e}",
                    }
                ),
                400,
            )

        # Write to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(safe_code)
            script_path = f.name

        script_dir = os.path.dirname(script_path)

        quality = data.get("quality", "medium")
        quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}.get(
            quality, "-qm"
        )
        out_dir = tempfile.mkdtemp()

        # Copy scene.py NEXT TO THE SCRIPT so "from scene import CScene" works
        scene_src = MANIM_DIR / "scene.py"
        print("DEBUG script_path:", script_path)
        print("DEBUG script_dir:", script_dir)
        print("DEBUG MANIM_DIR:", MANIM_DIR)
        print("DEBUG scene_src:", scene_src, "exists:", scene_src.exists())

        if scene_src.exists():
            shutil.copy(scene_src, os.path.join(script_dir, "scene.py"))
        else:
            print("WARNING: scene.py NOT FOUND at", scene_src)

        print(f"VIDEOGEN: Rendering video for material {material_id_str}...")
        cmd = [
            get_manim_command(),
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
            print("MANIM STDOUT:", proc.stdout)
            print("MANIM STDERR:", proc.stderr)
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

        video_path = find_video_file(out_dir, material_id_str)

        if proc.returncode != 0 and not video_path:
            combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
            return (
                jsonify(
                    {
                        "error": "Manim rendering failed",
                        "details": combined[:4000],
                    }
                ),
                500,
            )

        if not video_path:
            return jsonify({"error": "Rendered video not found"}), 500

        video_url = save_video_to_static(video_path, material_id_str)
        db.materials.update_one(
            {"_id": material_obj_id},
            {"$set": {"videoUrl": video_url, "videoGeneratedAt": datetime.utcnow()}},
        )

        return (
            jsonify(
                {"success": True, "videoUrl": video_url, "message": "Video generated"}
            ),
            200,
        )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video rendering timed out"}), 408
    except Exception as e:
        return (
            jsonify({"error": "Failed to generate video", "details": str(e)}),
            500,
        )
    finally:
        if script_path and os.path.exists(script_path):
            os.unlink(script_path)
        if out_dir and os.path.isdir(out_dir):
            shutil.rmtree(out_dir, ignore_errors=True)
