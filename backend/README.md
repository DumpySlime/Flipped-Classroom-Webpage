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