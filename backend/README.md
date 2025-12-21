# Flask MongoDB API

A RESTful API backend built with Flask that connects to a MongoDB database.

## Features

- RESTful API endpoints for CRUD operations on any MongoDB collection
- JWT-based authentication system
- **AI-Powered Material Generation** using Large Language Models
- LLM Chatbot
- Course Material Management
- MongoDB for file storage
- Error handling

### Development

1. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
  ```
  pip install -r requirements.txt
  ```
3. Environment configuration
   remove .example from .env.example, and input the required values

### Routes

## admin.py
   ```
   BP /admin
   ```

## ai.py
   ```
   BP /api/ai
   /ai-chat
   ```

## analytics.py
   ```
   BP /api/analytics
   /students
   /report
   ```

## auth.pyx
   ```
   BP /auth
   /api/register
   /api/login

   #testing
   /test-login
   ```

## db.py
   ```
   BP /db
   # Materials
   /material-add
   /material
   /material-delete
   # PPT
   /material/<file_id>/signed-url
   /public/pptx/<token>
   # User
   /user-add
   /user
   # Subject
   /subject-add
   /subject
   # Question
   /question-add

   ```

## llm.py
   ```
   BP /api
   /ppt/create
   /ppt/progress

   #testing
   /llm/query
   /test/xf-auth
   /test/ppt/create
   /test/ppt/progress
   /test/ppt/reset
   ```