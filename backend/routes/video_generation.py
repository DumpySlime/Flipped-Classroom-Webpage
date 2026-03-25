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

def get_all_slides(material: dict) -> list[dict]:
    """
    Normalize material['slides'] into a flat list[dict], without skipping.
    """
    raw = material.get("slides", [])

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
    return all_slides


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
    For a material with at least 6 slides (intro + 4 content + conclusion),
    generate 4 separate videos, one for each of slides 2–5.
    """
    quality_flag = "-qm"
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

        all_slides = get_all_slides(material)
        language = material.get('attribute').get('language')
        if len(all_slides) < 6:
            return jsonify({
                "error": "Need at least 6 slides (intro, 4 content, conclusion)"
            }), 400
            
        content_slides = all_slides[1:5]
        topic = material.get("topic") or material.get("title") or "Educational Topic"

        quality = data.get("quality", "medium")
        quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}.get(
            quality, "-qm"
        )

        videos = []

        for offset, slide in enumerate(content_slides, start=2):
            slide_number = offset  # 2,3,4,5
            slide_text = f"Topic: {topic}\n\n{slide['title']}\n{slide['content']}"
            print(f"DEBUG slide {slide_number} text length:", len(slide_text))
            print(f"DEBUG slide {slide_number} text first 300 chars:\n", slide_text[:300])

            manim_code = generate_animation(title, slide_text, language)
            if not manim_code:
                return jsonify({
                    "error": f"Failed to generate animation code for slide {slide_number}"
                }), 500

            # sanitize
            safe_code = manim_code
            safe_code = re.sub(r"```.*?```", "", safe_code, flags=re.IGNORECASE)
            safe_code = safe_code.encode("utf-8", errors="replace").decode(
                "utf-8", errors="replace"
            )
            safe_code = safe_code.replace("MathTex", "Text")
            safe_code = "\n".join(line.rstrip() for line in safe_code.splitlines()).lstrip()
            safe_code = re.sub(r"\.RightAngle", "", safe_code)
            
            for bad, good in {
                "→": "->",
                "←": "<-",
                "⇒": "=>",
            }.items():
                safe_code = safe_code.replace(bad, good)

            try:
                compile(safe_code, f"generated-manim-{slide_number}", "exec")
            except SyntaxError as e:
                return jsonify({
                    "error": f"Generated Manim code has a syntax error for slide {slide_number}",
                    "details": f"{e.__class__.__name__}: {e}",
                }), 400

            script_path = None
            out_dir = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".py", delete=False, encoding="utf-8"
                ) as f:
                    f.write(safe_code)
                    script_path = f.name

                script_dir = os.path.dirname(script_path)
                out_dir = tempfile.mkdtemp()

                # copy scene.py
                scene_src = MANIM_DIR / "scene.py"
                if scene_src.exists():
                    shutil.copy(scene_src, os.path.join(script_dir, "scene.py"))
                else:
                    print("WARNING: scene.py NOT FOUND at", scene_src)

                output_id = f"{material_id_str}_slide{slide_number}"
                print(f"VIDEOGEN: Rendering video for material {material_id_str}, slide {slide_number}...")
                cmd = [
                    get_manim_command(),
                    quality_flag,
                    script_path,
                    "EducationalVideo",
                    "-o",
                    f"video_{output_id}",
                ]

                proc = subprocess.run(
                    cmd,
                    cwd=out_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=600,
                )
                print(f"MANIM STDOUT (slide {slide_number}):", proc.stdout)
                print(f"MANIM STDERR (slide {slide_number}):", proc.stderr)

                video_path = find_video_file(out_dir, output_id)

                if proc.returncode != 0 and not video_path:
                    combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
                    return jsonify({
                        "error": f"Manim rendering failed for slide {slide_number}",
                        "details": combined[:4000],
                    }), 500

                if not video_path:
                    return jsonify({
                        "error": f"Rendered video not found for slide {slide_number}"
                    }), 500

                video_url = save_video_to_static(video_path, output_id)
                raw = material.get("slides", {})
                if isinstance(raw, dict) and "slides" in raw:
                    idx = slide_number - 1  # slide_number is 2..5
                    field_path = f"slides.slides.{idx}.video_url"
                    db.materials.update_one(
                        {"_id": material_obj_id},
                        {"$set": {field_path: video_url}},
                    )
                videos.append({
                    "slide": slide_number,
                    "videoUrl": video_url,
                })

            finally:
                if script_path and os.path.exists(script_path):
                    os.unlink(script_path)
                if out_dir and os.path.isdir(out_dir):
                    shutil.rmtree(out_dir, ignore_errors=True)

        raw = material.get("slides", {})
        if isinstance(raw, dict) and "slides" in raw:
            slides_doc = raw.get("slides") or []
            for part in videos:
                slide_num = part["slide"] 
                url = part["videoUrl"]
                idx = slide_num - 1
                if 0 <= idx < len(slides_doc):
                    slides_doc[idx]["video_url"] = url

            db.materials.update_one(
                {"_id": material_obj_id},
                {
                    "$set": {
                        "slides.slides": slides_doc,
                        "videoGeneratedAt": datetime.utcnow(),
                    }
                },
            )
        else:
            slides_list = raw if isinstance(raw, list) else []
            for part in videos:
                slide_num = part["slide"]
                url = part["videoUrl"]
                idx = slide_num - 1
                if 0 <= idx < len(slides_list):
                    slides_list[idx]["video_url"] = url

            db.materials.update_one(
                {"_id": material_obj_id},
                {
                    "$set": {
                        "slides": slides_list,
                        "videoGeneratedAt": datetime.utcnow(),
                    }
                },
            )

        db.materials.update_one(
            {"_id": material_obj_id},
            {
                "$set": {
                    "videoParts": videos,
                    "videoGeneratedAt": datetime.utcnow(),
                }
            },
        )

        return jsonify({
            "success": True,
            "videos": videos,
            "message": "Videos generated for slides 2–5",
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video rendering timed out"}), 408
    except Exception as e:
        return jsonify({"error": "Failed to generate video", "details": str(e)}), 500
