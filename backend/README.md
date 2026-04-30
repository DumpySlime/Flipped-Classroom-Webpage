# Flipped Classroom — Backend (Final / Project Closure)

This repository contains the Flask backend for the Flipped Classroom Web App. It provides RESTful CRUD for course materials, JWT auth, AI-assisted content generation, an LLM chatbot, video generation (Manim), analytics and token usage tracking.

Quick status: production-ready prototype. Core integrations (MongoDB, DeepSeek AI, Manim) implemented. See "Notes & Limitations" below.

## Table of Contents
- Overview
- Components (what they are & how they work)
- Major endpoints
- Dev / run instructions
- Environment variables
- Testing & debugging
- Notes & limitations

---

## Overview
The backend is a Flask application exposing blueprints for authentication, material management, AI generation, analytics and video generation. MongoDB stores materials, questions, users and analytics. DeepSeek (LLM) is used for slide/question/report generation. Manim is used to render short educational animations (video parts) from generated code.

---

## Components

- app.py
  - Flask app bootstrap, JWT manager, CORS, PyMongo initialization.
  - Registers blueprints and calls initialization functions for modules that need DB/app context.

- config.py
  - Central app configuration (env-driven). Loads DEEPSEEK and Mongo config.

- routes/
  - admin.py
    - Admin helper(s). Small authorization checks for admin-only tasks.
  - auth.py
    - User registration & login endpoints (/api/register, /api/login).
    - Password hashing via Flask-Bcrypt and JWT token generation.
  - db.py
    - Core CRUD for materials, questions, subjects, users, student submissions.
    - Routes: /db/material-add, /db/material, /db/material-update, /db/material-delete, /db/question-add, /db/question, /db/student-answers, etc.
    - Soft-deletes (is_deleted) and ownership/role checks implemented.
  - ai.py
    - LLM-powered endpoints and helpers: ai-chat (Socratic tutor streaming), generate-question, grade-short-answer, report generation functions (generate_performance_report & fallback).
    - Integrates with DeepSeek API, handles streaming responses and JSON parsing.
  - llm.py
    - Material generation via DeepSeek for slides (material_create). Calls internal /db/material-add and /db/material-update endpoints so the material lifecycle is persisted.
    - Retry-safe HTTP session for reliable API calls.
  - analytics.py
    - Student analytics endpoints and AI report orchestration.
    - Aggregation pipelines to compute progress, averages, recent performance and to filter out soft-deleted materials.
  - video_generation.py
    - Orchestrates slide → Manim code → render → saved mp4 workflow.
    - Uses utils.manim.generate_animation to call LLM for storyboard + code, validates and renders via manim CLI, stores videos in static/generated_videos and updates material doc with video_url.
    - Skips intro/conclusion slides and "example" slides by design.

- utils/
  - manim/
    - generate_animation.py
      - Orchestrates LLM calls: storyboard -> manim code -> review -> validate.
      - Uses DeepSeek endpoints, has retries, token usage tracking and fallback code.
    - scene.py
      - Manim scene template (CScene) with helper methods used by generated code.
  - token_usage.py
    - TokenUsageTracker: session-based token accounting across endpoints (start_session, add_usage, end_tracking).
    - Helper get_token_usage(result) to parse API responses.
  - logger.py
    - Central logging setup that writes to backend/logs and console.

- Logs
  - backend/logs — captures per-module logs (created via utils.logger).

---

## Major Endpoints (summary)

- Authentication
  - POST /auth/api/register
  - POST /auth/api/login
  - GET /auth/test-login (JWT required)

- Materials & DB
  - POST /db/material-add — create material (initial record for generated materials)
  - GET /db/material — query materials
  - PUT /db/material-update — update slides/status
  - DELETE /db/material-delete — soft-delete material
  - POST /db/question-add, GET /db/question
  - POST /db/student-answers-submit, GET /db/student-answers

- AI & LLM
  - POST /api/llm/material/create — generate teaching slides (DeepSeek)
  - POST /api/ai/ai-chat — streaming Socratic LLM chat (SSE)
  - POST /api/ai/generate-question — generate question sets (DeepSeek)
  - POST /api/ai/grade-short-answer — AI-assisted grading
  - Analytics -> POST /api/analytics/report (per-student report) and /api/analytics/report/all

- Video generation
  - POST /api/generate-video/generate — generate per-slide videos (video parts) and update materials

---

## Data model (collections)
- users: username, password (hashed), role (admin/teacher/student), profile fields
- materials: subject_id, attribute (topic, subtopic, form, language), slides (JSON), status, create_type, uploaded_by, is_deleted
- questions: material_id, question_content (JSON), created_by, is_deleted
- student_answers: student_id, material_id, answers[], total_score, submission_time, status
- subjects, topics, subject_members: subject management
- ai_reports: student_id, report_en, report_zh, generated_at

---

## How AI flows work (high level)
1. Teacher requests material generation (/api/llm/material/create).
2. Endpoint creates an initial DB material record via /db/material-add (status: generating).
3. LLM (DeepSeek) is called to produce slide JSON (call_deepseek_api). Token usage tracked via token_tracker.
4. Material is updated via /db/material-update with slides and status completed.
5. For each slide requiring video, video_generation calls utils.manim.generate_animation:
   - call_storyboard -> call_animation -> review_animation_code -> validate_code
   - On success the generated Python code is rendered by calling manim (subprocess), mp4 saved and DB updated.

---

## Development & Run (local)

1. Create & activate virtualenv (Windows):
   - python -m venv venv
   - venv\Scripts\activate

2. Install:
   - pip install -r requirements.txt

3. Environment:
   - Copy .env.example -> .env and set:
     - MONGO_URI, JWT_SECRET_KEY, OFFICE_SECRET_KEY
     - DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
     - PUBLIC_BASE_URL (for internal callback routes)
   - If using DeepSeek disable or set fallback usage for offline.

4. Run:
   - From backend folder:
     - python app.py
   - App listens on 0.0.0.0:5000 by default (dev).

Notes: Manim rendering requires manim installed and accessible in PATH. On macOS the manim binary path detection is attempted for Homebrew.

---

## Testing & Debugging
- Use Postman / curl to call endpoints with Authorization: Bearer <access_token>.
- AI endpoints can be tested with fallback behavior by omitting DEEPSEEK_API_KEY.
- Logs are under backend/logs/<module>.log.
- For video generation, inspect temporary directories printed in logs when rendering fails.

---

## Notes & Limitations
- DeepSeek calls are external — reliability and quota depend on the provider. Fallback templates provided.
- Manim rendering is resource and time intensive; render calls use subprocess with timeouts; rendering on constrained environments may fail.
- AI outputs are not fully sanitized — some manual review needed for production use.
- Security: Basic JWT + role checks exist but further hardening (rate-limiting, input sanitization) recommended.
- Some helper functions and templates contain placeholders that can be completed/trimmed for final production.

---

## Closing / Handover
- All major flows implemented: create material (AI), create questions (AI), generate per-slide videos (LLM → Manim), student submissions, analytics and AI reports.
- To continue maintenance:
  - Add end-to-end tests for generation & rendering.
  - Add CI for linting and unit tests.
  - Replace DeepSeek placeholders with production credentials and monitor token usage.

---

### Routes

## admin.py
   ```
   BP /admin
   ```

## ai.py
   ```
   BP /api/ai
   /ai-chat
      - data
      - message
   ```

## analytics.py
   ```
   BP /api/analytics
   /students
   /report
      - data
      - student_id
   ```

## auth.pyx
   ```
   BP /auth
   /api/register
      - user_info
         - username
         - password
         - role
         - firstName
         - lastName
   /api/login
      - username
      - password


   #testing
   /test-login
   ```

## db.py
   ```
   BP /db
   # Materials
   /material-add
      - file
      - subject_id
      - topic
      - create_type
      - user_id (optional)
   /material
      - material_id
      - filename
      - subject_id
      - topic
      - uploaded_by
   /material-delete
      - material_id
   # PPT
   /material/<file_id>/signed-url
   /public/pptx/<token>
      - f_id
   # User
   /user-add
      - username
      - password
      - firstName
      - lastName
      - role
   /user
      - usrname
      - role
      - firstName
      - lastName
   # Subject
   /subject-add
      - data
         - subject
         - topics
         - teacher_ids
         - student_ids
   /subject
      - id
      - subject
      - teacher_id
      - student_id
   # Question
   /question-add
      - data
         - subject_id
         - topic
         - question_text
   ```

## llm.py
   ```
   BP /api/llm
   /ppt/create
      - form
         - subject
         - topic
         - instruction
         - template_id
         - author
         - language
         - subject_id
         - query
   /ppt/progress
      - data
         - subject
         - topic

   #testing
   /llm/query
   /test/xf-auth
   /test/ppt/create
   /test/ppt/progress
   /test/ppt/reset
   ```
