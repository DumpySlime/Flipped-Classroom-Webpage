from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from bson import ObjectId
from datetime import datetime
import subprocess
import tempfile
import os
import shutil
import sys
from pathlib import Path
from utils.manim.generate_animation import generate_animation


video_gen_bp = Blueprint("video_generation", __name__)

db = None

BASE_DIR = Path(__file__).resolve().parent.parent
MANIM_DIR = BASE_DIR / "utils" / "manim"
SCENE_PATH = MANIM_DIR / "scene.py"


def init_video_generation(database, app):
    global db
    db = database
    print("VIDEOGEN: Video generation module initialized")


def get_manim_command() -> str:
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
        if len(all_slides) < 6:
            return jsonify({
                "error": "Need at least 6 slides (intro, 4 content, conclusion)"
            }), 400

        content_slides = all_slides[1:5]  # slides index 1,2,3,4 → slide numbers 2,3,4,5
        topic = material.get("topic") or material.get("title") or "Educational Topic"

        quality = data.get("quality", "medium")
        quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}.get(quality, "-qm")

        videos = []

        for offset, slide in enumerate(content_slides, start=2):
            slide_number = offset  # 2, 3, 4, 5
            slide_text = f"Topic: {topic}\n\n{slide['title']}\n{slide['content']}"
            print(f"DEBUG slide {slide_number} text length:", len(slide_text))
            print(f"DEBUG slide {slide_number} text first 300 chars:\n", slide_text[:300])

            manim_code = generate_animation(slide_text, review_code=False)
            if not manim_code:
                return jsonify({
                    "error": f"Failed to generate animation code for slide {slide_number}"
                }), 500

            # UTF-8 sanitize and strip trailing whitespace
            safe_code = manim_code.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            safe_code = "\n".join(line.rstrip() for line in safe_code.splitlines()).lstrip()

            # Early syntax check before spending time on Manim subprocess
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

                # Copy scene.py boilerplate to both dirs
                scene_src = MANIM_DIR / "scene.py"
                if scene_src.exists():
                    shutil.copy(scene_src, os.path.join(script_dir, "scene.py"))
                    shutil.copy(scene_src, os.path.join(out_dir, "scene.py"))
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
                print(f"MANIM RETURN CODE (slide {slide_number}):", proc.returncode)
                print(f"MANIM STDOUT (slide {slide_number}):", proc.stdout[-3000:])
                print(f"MANIM STDERR (slide {slide_number}):", proc.stderr[-3000:])

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
                videos.append({
                    "slide": slide_number,
                    "videoUrl": video_url,
                })

            finally:
                if script_path and os.path.exists(script_path):
                    os.unlink(script_path)
                if out_dir and os.path.isdir(out_dir):
                    shutil.rmtree(out_dir, ignore_errors=True)

        # Re-fetch fresh material to avoid stale slide data
        material = db.materials.find_one({"_id": material_obj_id})
        raw = material.get("slides", {})

        if isinstance(raw, dict) and "slides" in raw:
            slides_doc = raw.get("slides") or []
            for part in videos:
                idx = part["slide"] - 1  # slide 2 → index 1, slide 3 → index 2, etc.
                if 0 <= idx < len(slides_doc):
                    slides_doc[idx]["video_url"] = part["videoUrl"]

            db.materials.update_one(
                {"_id": material_obj_id},
                {
                    "$set": {
                        "slides.slides": slides_doc,
                        "videoParts": videos,
                        "videoGeneratedAt": datetime.utcnow(),
                    }
                },
            )
        else:
            slides_list = raw if isinstance(raw, list) else []
            for part in videos:
                idx = part["slide"] - 1
                if 0 <= idx < len(slides_list):
                    slides_list[idx]["video_url"] = part["videoUrl"]

            db.materials.update_one(
                {"_id": material_obj_id},
                {
                    "$set": {
                        "slides": slides_list,
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