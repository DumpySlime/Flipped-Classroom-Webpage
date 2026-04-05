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
from utils.token_usage import token_tracker

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
    Generates separate videos for content slides.
    Rules:
    1. Ignores the first slide (Intro) and the last slide (Conclusion).
    2. Ignores any slide where slideType == "example".
    """
    quality_flag = "-qm"
    try:
        if db is None:
            return jsonify({"error": "Database not initialized"}), 500

        try:
            token_tracker.start_session_tracking()
            print("[TOKEN_TRACKER] Session tracking continued for video generation")
        except Exception as te:
            print(f"[TOKEN_TRACKER] Warning: {te}")
            import traceback
            traceback.print_exc()

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

        # 1. Get raw slides to check for slideType
        raw_data = material.get("slides", [])
        if isinstance(raw_data, dict) and "slides" in raw_data:
            raw_slides_list = raw_data.get("slides") or []
        else:
            raw_slides_list = raw_data if isinstance(raw_data, list) else []

        if len(raw_slides_list) < 3:
            return jsonify({
                "error": "Need at least 3 slides (intro, content, conclusion) to process"
            }), 400

        # 2. Extract language and topic
        language = "English"
        try:
            language = material.get('attribute', {}).get('language', 'English')
        except:
            pass
        topic = material.get("topic") or material.get("title") or "Educational Topic"

        quality = data.get("quality", "medium")
        quality_flag = {"low": "-ql", "medium": "-qm", "high": "-qh"}.get(quality, "-qm")

        videos = []

        # 3. Iterate through slides, skipping first [0] and last [-1]
        for idx in range(1, len(raw_slides_list) - 1):
            slide_doc = raw_slides_list[idx]
            slide_number = idx + 1 # 1-based index for UI/logging

            # RULE: Skip if slideType is 'example'
            if isinstance(slide_doc, dict) and slide_doc.get("slideType") == "example":
                print(f"VIDEOGEN: Skipping slide {slide_number} because type is 'example'")
                continue

            # Prep slide content for Manim
            subtitle = slide_doc.get("subtitle", f"Slide {slide_number}")
            contents = slide_doc.get("content", "")
            content_text = " ".join(str(c) for c in contents) if isinstance(contents, list) else str(contents)
            
            slide_text = f"Topic: {topic}\n\n{subtitle}\n{content_text}"

            # Generate Manim code
            result = generate_animation(subtitle, slide_text, language)
            if not result:
                continue # Or handle as error
            result, token_usage, time = generate_animation(slide_title, slide_text, language)
            
            # Track token usage for this slide
            try:
                token_tracker.add_usage(token_usage, f"Slide {slide_number} Video Generation", endpoint="/api/generate-video/generate")
                print(f"[TOKEN_TRACKER] Token usage for slide {slide_number}: {token_usage}")
            except Exception as track_err:
                print(f"[TOKEN_TRACKER] Warning: Could not track usage: {track_err}")
            
            if result is None or len(result) < 1:
                return jsonify({
                    "error": f"Failed to generate animation code for slide {slide_number}"
                }), 500
            
            manim_code = result[0] if isinstance(result, tuple) else result
            
            # Sanitize and format code
            safe_code = manim_code.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            safe_code = "\n".join(line.rstrip() for line in safe_code.splitlines()).lstrip()
            safe_code = safe_code.replace("MathTex(", "Text(").replace("Tex(", "Text(")

            # Early syntax check
            try:
                compile(safe_code, f"gen-{slide_number}", "exec")
            except SyntaxError as e:
                print(f"Syntax Error in slide {slide_number}: {e}")
                continue

            script_path = None
            out_dir = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                    f.write(safe_code)
                    script_path = f.name

                script_dir = os.path.dirname(script_path)
                out_dir = tempfile.mkdtemp()

                scene_src = MANIM_DIR / "scene.py"
                if scene_src.exists():
                    shutil.copy(scene_src, os.path.join(script_dir, "scene.py"))
                    shutil.copy(scene_src, os.path.join(out_dir, "scene.py"))

                output_id = f"{material_id_str}_slide{slide_number}"
                cmd = [get_manim_command(), quality_flag, script_path, "EducationalVideo", "-o", f"video_{output_id}"]

                proc = subprocess.run(cmd, cwd=out_dir, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=600)

                video_path = find_video_file(out_dir, output_id)
                if video_path:
                    video_url = save_video_to_static(video_path, output_id)
                    videos.append({
                        "slide": slide_number,
                        "videoUrl": video_url,
                    })
            finally:
                if script_path and os.path.exists(script_path): os.unlink(script_path)
                if out_dir and os.path.isdir(out_dir): shutil.rmtree(out_dir, ignore_errors=True)

        # 4. Update Database
        if isinstance(raw_data, dict) and "slides" in raw_data:
            slides_doc = raw_data.get("slides") or []
            for part in videos:
                idx = part["slide"] - 1
                if 0 <= idx < len(slides_doc):
                    slides_doc[idx]["video_url"] = part["videoUrl"]
            
            db.materials.update_one(
                {"_id": material_obj_id},
                {"$set": {"slides.slides": slides_doc, "videoParts": videos, "videoGeneratedAt": datetime.utcnow()}}
            )
        else:
            slides_list = raw_data if isinstance(raw_data, list) else []
            for part in videos:
                idx = part["slide"] - 1
                if 0 <= idx < len(slides_list):
                    slides_list[idx]["video_url"] = part["videoUrl"]

            db.materials.update_one(
                {"_id": material_obj_id},
                {"$set": {"slides": slides_list, "videoParts": videos, "videoGeneratedAt": datetime.utcnow()}}
            )
        
        # End tracking after all videos are generated
        try:
            token_tracker.end_tracking()
            print("[TOKEN_TRACKER] Session ended after video generation")
        except Exception as e:
            print(f"[TOKEN_TRACKER] Warning: Could not end session: {e}")
            
        return jsonify({
            "success": True,
            "videos": videos,
            "message": f"Generated {len(videos)} videos (skipped intro, conclusion, and examples)",
        }), 200

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Video rendering timed out"}), 408
    except Exception as e:
        return jsonify({"error": "Failed to generate video", "details": str(e)}), 500