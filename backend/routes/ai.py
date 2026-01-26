from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import re
import json

ai_bp = Blueprint('ai', __name__)

DEEPSEEK_API_KEY = None
DEEPSEEK_MODEL = None
DEEPSEEK_BASE_URL = None

@ai_bp.record_once
def on_load(state):
    global DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
    app = state.app
    DEEPSEEK_API_KEY = app.config.get("DEEPSEEK_API_KEY")   
    DEEPSEEK_MODEL = app.config.get("DEEPSEEK_MODEL")   
    DEEPSEEK_BASE_URL = app.config.get("DEEPSEEK_BASE_URL")   
    print(f"[DEEPSEEK] API Key loaded: {'YES' if DEEPSEEK_API_KEY else 'NO key in .env'}")

BAD_KEYWORDS = [
    "answer", "solution"
]

DEFENSIVE_REPLY = (
    "You are being a nasty bad boy. Its a no no for directly giving answers to assignment questions. "
)

def is_assignment_question(message: str) -> bool:
    return any(keyword in message.lower() for keyword in BAD_KEYWORDS)

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def smart_wrap_latex(text: str) -> str:
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('$$') or stripped.startswith('\\('):
            result.append(line)
            continue
        if re.search(r'\\frac|\\times|\\cdot|\^|_|\{|\}', line):
            if stripped.startswith('[') and stripped.endswith(']'):
                line = line.replace('[', '\\(', 1).replace(']', '\\)', 1)
            elif '{' in stripped and '}' in stripped:
                line = re.sub(r'\{([^}]+)\}', r'$$\1$$', line)
        result.append(line)
    return '\n'.join(result)

@ai_bp.route('/ai-chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error': 'No messages'}), 400

    last_user_msg = next((m['content'] for m in reversed(messages) if m['role'] == 'user'), '')
    if is_assignment_question(last_user_msg):
        return Response(
            (f"data: {json.dumps({'content': DEFENSIVE_REPLY})}\n\n" +
            "data: [DONE]\n\n"),
            mimetype='text/event-stream'
        )

    if not DEEPSEEK_API_KEY:
        return jsonify({'error': 'DEEPSEEK_API_KEY missing in .env'}), 400

    def generate():
        try:
            system_msg = {
                "role": "system",
                "content": (
                    "You are a helpful assistant.Which helps users with their questions. "
                    "However, don't provide any answers related to assignments, homework, exams, or tests. "
                    "You can answer them in traditional chinese(cantonese and easy english). "
                    "ALso if the student ask or request some thing to solve or answer please don't provide answer for them"
                )
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [system_msg, *messages], 
                "temperature": 0.7,
                "stream": True
            }

            with requests.post(
                "https://api.deepseek.com/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                stream=True,
                timeout=90
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        decoded = line.decode('utf-8').strip()
                        if decoded.startswith("data: "):
                            data = decoded[6:]
                            if data == "[DONE]": continue
                            try:
                                json_data = json.loads(data)
                                delta = json_data['choices'][0]['delta']
                                if 'content' in delta:
                                    content = smart_wrap_latex(delta['content'])
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except: continue
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_msg = "DeepSeek 連線失敗"
            if "402" in str(e): error_msg = "DeepSeek 餘額不足！充值 $1 USD！"
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype='text/event-stream')

@ai_bp.route('/generate-question', methods=['POST'])
@jwt_required()
def generate_question():

    if not DEEPSEEK_API_KEY:
        return jsonify({'error': 'DEEPSEEK_API_KEY missing in .env'}), 400

    topic = request.form.get('topic')
    material_id = request.form.get('material_id')

    print(f"Content-Type: {request.content_type}")
    print(f"Form fields: {dict(request.form)}")
    print(f"material_id from form: '{request.form.get('material_id')}'")

    if not material_id or not topic:
        return jsonify({'error': 'material_id and topic are required'}), 400

    uploaded_by = get_jwt_identity()
    print(f"Generating questions for material:{material_id} , topic: {topic}")

    content = None
    
    try:
        system_prompt = {
            "role": "system",
            "content": f'''
                You are an expert educational content creator.

                Format your response as a JSON object with this structure:
                {{
                    "questions": [
                        {{
                            "questionText": "Question here",
                            "questionType": "multiple_choice" or "short_answer",
                            "options": ["Option 1", "Option 2", "Option 3", "Option 4"], // only for multiple choice
                            "correctAnswer": 1, // index (0-3) for MC, text for short answer
                            "explanation": "Why this is the correct approach and brief reasoning",
                            "stepByStepSolution": "Step 1: First analyze... Step 2: Then calculate... Step 3: Final result...",
                            "learningObjective": "What student learns",
                            "points": 5
                        }}
                    ],
                    "topic": "{{topic}}"
                }}

                IMPORTANT: For multiple choice questions, correctAnswer must be an index (0, 1, 2, or 3) corresponding to the position in the options array.
                Do NOT include your thinking process, reasoning steps, or any references in the output. Only return the required fields in the specified JSON format.
                Make sure questions are educational, accurate, and appropriate for the beginning level.
                '''
        }

        user_prompt = {
            "role": "user",
            "content": f'''
                Generate 3 educational questions with detailed solutions on the topic: {topic}.
                
                Requirements:
                - Main topic: {topic}
                - Difficulty level: easy
                - Learning objectives: introduction to the topic
                - Question types to include: Multiple Choice and Short Answer
                - Number of questions: 3

                For each question, provide:
                1. Clear, well-formulated question text
                2. If multiple choice: 4 options with one correct answer
                3. Detailed step-by-step solution/explanation
                4. Learning objective addressed
                '''
        }

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [system_prompt, user_prompt], 
            "temperature": 1.3,
            "stream": False
        }

        with requests.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            stream=False,
            timeout=90
        ) as resp:
            resp.raise_for_status()
            response = resp.json()
            content = response['choices'][0]['message']['content']
            print(f"Questions generated successfully: {content}")
            # Parse content as JSON
            try:
                if content.startswith("```"):
                    content = content[len("```json"):].strip()
                if content.endswith("```"):
                    content = content[:-len("```")].strip()
                content_json = json.loads(content)
            except json.JSONDecodeError as jde:
                print(f"JSON decode error: {str(jde)}")
                return jsonify({'error': 'Failed to parse generated content as JSON', 'details': str(jde)}), 500
            
        # Prepare to save question sets into /db/question-add
        try:
            base = request.host_url.rstrip('/')
            auth_hdr = {}
            auth = request.headers.get("Authorization")
            if auth:
                auth_hdr["Authorization"] = auth
            
            session = get_session()
            url = f"{base}/db/question-add"

            print(f"Preparing to post questions via /db/question-add route at {url}")
            print(f"Topic: {topic}, User ID: {uploaded_by}")
        except Exception as e:
            raise Exception(f"Error preparing url: {str(e)}")

        
        # Make the POST request through /db/question-add
        try:
            # Prepare file object
            data = {
                "material_id": str(material_id) if material_id else "",
                # "topic": topic,
                "user_id": uploaded_by,
                "question_content": content_json,
                "create_type": "generated"
            }

            resp = session.post(
                url,
                json=data,
                headers=auth_hdr,
                timeout=30
            )
            resp.raise_for_status()
            question_result = resp.json()

            print(f"Material successfully posted via /db/question-add: {question_result}")

            return question_result
        except Exception as e:
            raise Exception(f"Failed to save questions via /db/question-add route: {str(e)}")

    except Exception as e:
        error_msg = "DeepSeek 連線失敗"
        if "402" in str(e): 
            error_msg = "DeepSeek 餘額不足！充值 $1 USD！"
        return jsonify({'error': error_msg, 'details': str(e)}), 500
    

# Add these functions to your existing ai.py file
# AI report generation for student analytics - English only

def generate_performance_report(analytics_data):
    """
    Generate AI-driven performance report using DeepSeek
    Called by analytics.py to create student performance reports
    
    Args:
        analytics_data: dict containing student statistics
    
    Returns:
        str: Markdown formatted performance report
    """
    if not DEEPSEEK_API_KEY:
        return generate_fallback_report(analytics_data)
    
    student_name = analytics_data['student_name']
    total_submissions = analytics_data['total_submissions']
    avg_score = analytics_data['avg_score']
    max_score = analytics_data['max_score']
    min_score = analytics_data['min_score']
    progress_percentage = analytics_data['progress_percentage']
    materials_completed = analytics_data['materials_completed']
    total_materials = analytics_data['total_materials']
    trend = analytics_data['trend']
    recent_performance = analytics_data['recent_performance']
    
    # Prepare prompt for DeepSeek AI
    user_prompt = f"""Generate a comprehensive academic performance report for student: {student_name}

**Performance Data:**
- Total Submissions: {total_submissions}
- Average Score: {avg_score:.1f}%
- Highest Score: {max_score}%
- Lowest Score: {min_score}%
- Course Progress: {progress_percentage:.1f}% ({materials_completed}/{total_materials} materials completed)
- Performance Trend: {trend}

**Recent Activity (Latest {len(recent_performance)} submissions):**
{chr(10).join([f"Score: {p['score']}%, Questions Answered: {p['questions']}, Date: {p['date']}" for p in recent_performance])}

**Report Requirements:**
Please provide a detailed analysis including:

1. **Performance Summary** - Brief overview of overall academic performance
2. **Strengths** - What the student excels at
3. **Areas for Improvement** - Specific weaknesses to address
4. **Actionable Recommendations** - 3-5 concrete steps for improvement

Format using markdown with ## headers. Be encouraging but honest. Focus on actionable insights."""

    try:
        system_msg = {
            "role": "system",
            "content": (
                "You are an experienced educational analyst and academic advisor. "
                "Provide constructive, encouraging, and actionable feedback to help students improve. "
                "Format your response in markdown with clear sections."
            )
        }
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [system_msg, {"role": "user", "content": user_prompt}],
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=90
        )
        
        response.raise_for_status()
        result = response.json()
        ai_report = result['choices'][0]['message']['content'].strip()
        
        print(f"[ANALYTICS] DeepSeek AI report generated successfully for {student_name}")
        return ai_report
        
    except Exception as ai_error:
        print(f"[ANALYTICS] DeepSeek API error: {str(ai_error)}")
        return generate_fallback_report(analytics_data)


def generate_fallback_report(analytics_data):
    """
    Generate a template-based report when AI is unavailable
    
    Args:
        analytics_data: dict containing student statistics
    
    Returns:
        str: Markdown formatted performance report in English
    """
    student_name = analytics_data['student_name']
    avg_score = analytics_data['avg_score']
    max_score = analytics_data['max_score']
    total_submissions = analytics_data['total_submissions']
    progress_percentage = analytics_data['progress_percentage']
    materials_completed = analytics_data['materials_completed']
    total_materials = analytics_data['total_materials']
    trend = analytics_data['trend']
    
    # Determine performance level
    if avg_score >= 80:
        performance_level = "Excellent"
        encouragement = "Keep up the excellent work!"
    elif avg_score >= 70:
        performance_level = "Good"
        encouragement = "Continue your efforts!"
    elif avg_score >= 60:
        performance_level = "Satisfactory"
        encouragement = "Focus on improvement areas!"
    else:
        performance_level = "Needs Improvement"
        encouragement = "Let's work together to improve!"
    
    report = f"""## Performance Summary

{student_name} has completed {total_submissions} submission(s) with an average score of {avg_score:.1f}%, showing **{performance_level}** performance.

Course Progress: {materials_completed}/{total_materials} materials completed ({progress_percentage:.1f}%)

Performance Trend: {trend}

---

## Strengths

- Achieved highest score of {max_score}%, demonstrating strong learning potential
- {"Maintaining steady progress" if progress_percentage >= 50 else "Started engaging with course materials"}
- Consistent participation with {total_submissions} completed submission(s)

---

## Areas for Improvement

"""
    
    # Add specific improvement areas based on performance
    if avg_score < 70:
        report += """- Average score needs improvement - focus on understanding fundamental concepts
- Review materials where performance was below expectations
"""
    
    if progress_percentage < 50:
        report += """- Course progress is behind - consider dedicating more time to studies
- Aim to complete remaining materials systematically
"""
    
    if trend == "declining":
        report += """- Declining trend detected - adjust study strategies promptly
- Identify recent challenges and address them proactively
"""
    
    if not (avg_score < 70 or progress_percentage < 50 or trend == "declining"):
        report += """- Maintain consistency across all materials
- Challenge yourself with more advanced topics
"""
    
    report += f"""
---

## Actionable Recommendations

1. **Review Mistakes**
   - Revisit quizzes with lower scores to understand errors
   - Take notes on commonly missed concepts

2. **Create a Study Plan**
   - Dedicate consistent daily study time
   - Set specific goals for each study session

3. **{"Strengthen Fundamentals" if avg_score < 70 else "Challenge Yourself"}**
   - {"Start with basic concepts and build gradually" if avg_score < 70 else "Explore advanced materials to expand knowledge"}
   - {"Focus on mastering core topics before moving forward" if avg_score < 70 else "Apply learned concepts to real-world problems"}

4. **Seek Support**
   - Ask teachers or peers for help when needed
   - Participate actively in class discussions

5. **Stay Motivated**
   - {encouragement}
   - Track your progress regularly

---

**Conclusion**: {"Continue on this path - you're doing well!" if avg_score >= 70 else "Every effort brings progress. Keep pushing forward!"}
"""
    
    return report


# Updated AI report generation with question analysis


# Updated AI report generation - Teacher-focused, concise format

def generate_performance_report(analytics_data):
    """
    Generate AI-driven performance report using DeepSeek
    Teacher-focused format with key metrics only
    
    Args:
        analytics_data: dict containing student statistics and question analysis
    
    Returns:
        str: Markdown formatted performance report
    """
    if not DEEPSEEK_API_KEY:
        return generate_fallback_report(analytics_data)
    
    student_name = analytics_data['student_name']
    total_submissions = analytics_data['total_submissions']
    avg_score = analytics_data['avg_score']
    max_score = analytics_data['max_score']
    min_score = analytics_data['min_score']
    progress_percentage = analytics_data['progress_percentage']
    materials_completed = analytics_data['materials_completed']
    total_materials = analytics_data['total_materials']
    trend = analytics_data['trend']
    recent_performance = analytics_data['recent_performance']
    total_questions = analytics_data.get('total_questions', 0)
    correct_count = analytics_data.get('correct_count', 0)
    incorrect_count = analytics_data.get('incorrect_count', 0)
    accuracy = analytics_data.get('accuracy', 0)
    incorrect_questions = analytics_data.get('incorrect_questions', [])
    
    # Format incorrect questions for AI analysis
    incorrect_questions_text = ""
    if incorrect_questions:
        incorrect_questions_text = "\n**Incorrect Questions Sample:**\n"
        for i, q in enumerate(incorrect_questions[:5], 1):
            incorrect_questions_text += f"\n{i}. {q['question_text']}\n"
            incorrect_questions_text += f"   Student answered: {q['user_answer']} | Correct: {q['correct_answer']}\n"
    
    # Prepare prompt for DeepSeek AI
    user_prompt = f"""Generate a concise teacher-focused performance analysis for student: {student_name}

**Metrics:**
- Submissions: {total_submissions} | Avg Score: {avg_score:.1f}% | Range: {min_score}-{max_score}%
- Progress: {progress_percentage:.1f}% ({materials_completed}/{total_materials} materials)
- Accuracy: {accuracy:.1f}% ({correct_count}/{total_questions} correct)
- Trend: {trend}

{incorrect_questions_text}

**Format Requirements:**
Keep it brief and factual. Use these sections only:

## Strengths
List 2-3 specific strengths based on data

## Areas for Improvement
List 2-3 specific weaknesses or knowledge gaps based on incorrect answers

## Most Common Errors
Identify the main patterns in mistakes (topics/concepts they struggle with)

No encouragement, conclusions, or recommendations. Keep it objective and data-focused."""

    try:
        system_msg = {
            "role": "system",
            "content": (
                "You are an educational data analyst providing objective performance reports for teachers. "
                "Be concise, factual, and focus only on observable patterns in the data. "
                "No motivational language or student-directed advice."
            )
        }
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [system_msg, {"role": "user", "content": user_prompt}],
            "temperature": 0.5,
            "stream": False
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=90
        )
        
        response.raise_for_status()
        result = response.json()
        ai_report = result['choices'][0]['message']['content'].strip()
        
        print(f"[ANALYTICS] DeepSeek AI report generated successfully for {student_name}")
        return ai_report
        
    except Exception as ai_error:
        print(f"[ANALYTICS] DeepSeek API error: {str(ai_error)}")
        return generate_fallback_report(analytics_data)


def generate_fallback_report(analytics_data):
    """
    Generate a template-based report when AI is unavailable
    Teacher-focused, concise format
    
    Args:
        analytics_data: dict containing student statistics
    
    Returns:
        str: Markdown formatted performance report
    """
    student_name = analytics_data['student_name']
    avg_score = analytics_data['avg_score']
    max_score = analytics_data['max_score']
    min_score = analytics_data['min_score']
    total_submissions = analytics_data['total_submissions']
    progress_percentage = analytics_data['progress_percentage']
    materials_completed = analytics_data['materials_completed']
    total_materials = analytics_data['total_materials']
    trend = analytics_data['trend']
    accuracy = analytics_data.get('accuracy', 0)
    incorrect_count = analytics_data.get('incorrect_count', 0)
    total_questions = analytics_data.get('total_questions', 0)
    incorrect_questions = analytics_data.get('incorrect_questions', [])
    
    report = f"""## Strengths

"""
    
    # Identify strengths
    strengths = []
    if avg_score >= 80:
        strengths.append(f"High average score of {avg_score:.1f}%")
    if max_score >= 90:
        strengths.append(f"Capable of high performance (max score: {max_score}%)")
    if progress_percentage >= 70:
        strengths.append(f"Strong engagement with {materials_completed}/{total_materials} materials completed")
    if accuracy >= 75:
        strengths.append(f"Good accuracy rate of {accuracy:.1f}%")
    if trend == "improving":
        strengths.append("Performance trend is improving over time")
    if total_submissions >= 5:
        strengths.append(f"Consistent participation with {total_submissions} submissions")
    
    if not strengths:
        strengths.append("Shows willingness to participate")
        if max_score > avg_score + 10:
            strengths.append("Demonstrates potential for higher performance")
    
    for strength in strengths[:3]:
        report += f"- {strength}\n"
    
    report += "\n---\n\n## Areas for Improvement\n\n"
    
    # Identify weaknesses
    weaknesses = []
    if avg_score < 70:
        weaknesses.append(f"Below-target average score ({avg_score:.1f}%)")
    if accuracy < 70:
        weaknesses.append(f"Low accuracy rate ({accuracy:.1f}%) - {incorrect_count}/{total_questions} incorrect")
    if progress_percentage < 50:
        weaknesses.append(f"Behind on course progress ({progress_percentage:.1f}%)")
    if trend == "declining":
        weaknesses.append("Performance declining in recent submissions")
    if max_score - min_score > 40:
        weaknesses.append(f"Inconsistent performance (range: {min_score}-{max_score}%)")
    if total_submissions < 3:
        weaknesses.append("Limited submission data for accurate assessment")
    
    if not weaknesses:
        weaknesses.append("Could improve consistency across all materials")
        if avg_score < 90:
            weaknesses.append("Room for score improvement in future assessments")
    
    for weakness in weaknesses[:3]:
        report += f"- {weakness}\n"
    
    report += "\n---\n\n## Most Common Errors\n\n"
    
    # Analyze common mistakes
    if incorrect_questions and len(incorrect_questions) >= 2:
        # Group by question type or topic if possible
        question_types = {}
        for q in incorrect_questions:
            q_type = q.get('question_type', 'Unknown')
            question_types[q_type] = question_types.get(q_type, 0) + 1
        
        if question_types:
            report += f"**Error distribution by type:**\n"
            for q_type, count in sorted(question_types.items(), key=lambda x: x[1], reverse=True):
                report += f"- {q_type}: {count} error(s)\n"
            report += "\n"
        
        report += f"**Sample incorrect questions:**\n"
        for i, q in enumerate(incorrect_questions[:3], 1):
            question_preview = q['question_text'][:80] + "..." if len(q['question_text']) > 80 else q['question_text']
            report += f"{i}. {question_preview}\n"
            report += f"   - Answered: {q['user_answer']} | Correct: {q['correct_answer']}\n"
    elif incorrect_count > 0:
        report += f"- {incorrect_count} incorrect answer(s) recorded\n"
        report += f"- Overall accuracy needs improvement ({accuracy:.1f}%)\n"
    else:
        report += "- No significant error patterns detected\n"
        report += "- All submitted answers were correct\n"
    
    return report
