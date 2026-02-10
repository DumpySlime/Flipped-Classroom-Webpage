# analytics.py - Student Analytics Backend

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime

analytics_bp = Blueprint('analytics', __name__)

# Global variables - initialized by app
db = None

def init_analytics(database):
    """Initialize the analytics blueprint with database connection"""
    global db
    db = database
    print("[ANALYTICS] Analytics module initialized")


@analytics_bp.route('/api/analytics/students', methods=['GET'])
@jwt_required()
def get_student_analytics():
    """
    Aggregate student performance data from student_answers collection
    Returns: List of students with their analytics metrics
    """
    try:
        # Get total number of materials for progress calculation
        total_materials_count = db.materials.count_documents({"is_deleted": {"$ne": True}})
        
        if total_materials_count == 0:
            total_materials_count = 1  # Prevent division by zero
        
        # Aggregation pipeline to calculate analytics per student
        pipeline = [
            # Match only submitted answers
            {
                "$match": {
                    "status": "submitted"
                }
            },
            # Group by student_id to aggregate their performance
            {
                "$group": {
                    "_id": "$student_id",
                    "total_submissions": {"$sum": 1},
                    "avg_score": {"$avg": "$total_score"},
                    "last_activity": {"$max": "$submission_time"},
                    "materials_attempted": {"$addToSet": "$material_id"}
                }
            },
            # Lookup student details from students collection
            {
                "$lookup": {
                    "from": "students",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "student_info"
                }
            },
            {"$unwind": {"path": "$student_info", "preserveNullAndEmptyArrays": True}},
            # Lookup user details (in case student info is in users collection)
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
            # Project final output with calculated fields
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "name": {
                        "$ifNull": [
                            "$student_info.name",
                            {"$ifNull": ["$user_info.username", "Unknown Student"]}
                        ]
                    },
                    "progress": {
                        "$round": [
                            {
                                "$multiply": [
                                    {"$divide": [
                                        {"$size": "$materials_attempted"},
                                        total_materials_count
                                    ]},
                                    100
                                ]
                            },
                            0
                        ]
                    },
                    "avgQuizScore": {"$round": ["$avg_score", 0]},
                    "lastActivity": "$last_activity",
                    "totalSubmissions": "$total_submissions"
                }
            },
            # Sort by last activity (most recent first)
            {"$sort": {"lastActivity": -1}}
        ]
        
        results = list(db.student_answers.aggregate(pipeline))
        
        # If no results, return empty array
        if not results:
            return jsonify([]), 200
        
        return jsonify(results), 200
        
    except Exception as e:
        print(f"Error in get_student_analytics: {str(e)}")
        return jsonify({"error": "Failed to fetch student analytics", "details": str(e)}), 500


@analytics_bp.route('/api/analytics/report', methods=['POST'])
@jwt_required()
def generate_ai_report():
    """
    Generate AI-driven performance report for a specific student
    Request body: { "student_id": "ObjectId_string" }
    This endpoint delegates to ai.py for AI report generation
    """
    try:
        data = request.get_json()
        student_id_str = data.get('student_id')
        
        if not student_id_str:
            return jsonify({"error": "student_id is required"}), 400
        
        # Convert string to ObjectId
        try:
            student_id = ObjectId(student_id_str)
        except:
            return jsonify({"error": "Invalid student_id format"}), 400
        
        # Fetch student information
        student = db.students.find_one({"_id": student_id})
        if not student:
            # Try users collection
            student = db.users.find_one({"_id": student_id})
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        student_name = student.get('name') or student.get('username', 'Student')
        
        # Fetch all submissions for this student
        submissions = list(db.student_answers.find({
            "student_id": student_id,
            "status": "submitted"
        }).sort("submission_time", -1))
        
        if not submissions:
            return jsonify({
                "report": f"## No Data Available\n\n{student_name} has not completed any quizzes or assignments yet. No performance data is available for analysis."
            }), 200
        
        # Calculate detailed statistics with question analysis
        analytics_data = calculate_student_statistics_with_questions(submissions, student_name)
        
        # Import ai_service from ai.py to generate report
        from routes.ai import generate_performance_report
        
        # Call AI service to generate report
        ai_report = generate_performance_report(analytics_data)
        
        return jsonify({"report": ai_report}), 200
        
    except Exception as e:
        print(f"Error in generate_ai_report: {str(e)}")
        return jsonify({"error": "Failed to generate report", "details": str(e)}), 500


def calculate_student_statistics_with_questions(submissions, student_name):
    """
    Calculate comprehensive statistics from student submissions
    Includes analysis of incorrect questions
    Returns dict with analytics data for AI report generation
    """
    total_submissions = len(submissions)
    scores = [s.get('total_score', 0) for s in submissions]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    
    # Get unique materials attempted
    materials_attempted = set(str(s.get('material_id')) for s in submissions)
    total_materials = db.materials.count_documents({"is_deleted": {"$ne": True}})
    
    # Calculate progress
    progress_percentage = (len(materials_attempted) / total_materials * 100) if total_materials > 0 else 0
    
    # Analyze incorrect answers with question details
    incorrect_questions = []
    correct_count = 0
    total_questions = 0
    
    for submission in submissions:
        answers = submission.get('answers', [])
        material_id = submission.get('material_id')
        
        for answer in answers:
            total_questions += 1
            is_correct = answer.get('is_correct', False)
            
            if is_correct:
                correct_count += 1
            else:
                # Fetch question details from questions collection
                question_id = answer.get('question_id', '')
                question_doc = db.questions.find_one({"material_id": material_id})
                
                if question_doc:
                    question_content = question_doc.get('question_content', {})
                    questions_list = question_content.get('questions', [])
                    
                    # Parse question_id to find the specific question
                    # Format: "material_id-index1-index2"
                    parts = question_id.split('-')
                    if len(parts) >= 3:
                        try:
                            q_index = int(parts[-1])
                            if q_index < len(questions_list):
                                question_data = questions_list[q_index]
                                incorrect_questions.append({
                                    "question_text": question_data.get('questionText', 'N/A'),
                                    "question_type": question_data.get('questionType', 'N/A'),
                                    "correct_answer": question_data.get('correctAnswer', 'N/A'),
                                    "user_answer": answer.get('user_answer', 'N/A'),
                                    "explanation": question_data.get('explanation', 'N/A')
                                })
                        except (ValueError, IndexError):
                            pass
    
    # Get recent activity (last 5 submissions)
    recent_submissions = submissions[:5]
    recent_performance = [
        {
            "score": s.get('total_score', 0),
            "date": s.get('submission_time', ''),
            "questions": len(s.get('answers', []))
        }
        for s in recent_submissions
    ]
    
    # Calculate improvement trend
    if len(scores) >= 2:
        recent_half_avg = sum(scores[:len(scores)//2]) / len(scores[:len(scores)//2])
        older_half_avg = sum(scores[len(scores)//2:]) / len(scores[len(scores)//2:])
        
        if recent_half_avg > older_half_avg + 5:
            trend = "improving"
        elif recent_half_avg < older_half_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient data"
    
    # Calculate accuracy
    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "student_name": student_name,
        "total_submissions": total_submissions,
        "avg_score": avg_score,
        "max_score": max_score,
        "min_score": min_score,
        "progress_percentage": progress_percentage,
        "materials_completed": len(materials_attempted),
        "total_materials": total_materials,
        "trend": trend,
        "recent_performance": recent_performance,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_count": total_questions - correct_count,
        "accuracy": accuracy,
        "incorrect_questions": incorrect_questions[:10]  # Limit to 10 most recent mistakes
    }


@analytics_bp.route('/api/analytics/student/<student_id>', methods=['GET'])
@jwt_required()
def get_student_detail(student_id):
    """
    Get detailed analytics for a specific student
    """
    try:
        student_obj_id = ObjectId(student_id)
        
        # Get all submissions
        submissions = list(db.student_answers.find({
            "student_id": student_obj_id
        }).sort("submission_time", -1))
        
        # Get student info
        student = db.students.find_one({"_id": student_obj_id}) or db.users.find_one({"_id": student_obj_id})
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        return jsonify({
            "student": {
                "id": student_id,
                "name": student.get('name') or student.get('username', 'Unknown')
            },
            "submissions": [
                {
                    "id": str(s.get('_id')),
                    "material_id": str(s.get('material_id')),
                    "score": s.get('total_score'),
                    "answers_count": len(s.get('answers', [])),
                    "submission_time": s.get('submission_time'),
                    "status": s.get('status')
                }
                for s in submissions
            ]
        }), 200
        
    except Exception as e:
        print(f"Error in get_student_detail: {str(e)}")
        return jsonify({"error": "Failed to fetch student details", "details": str(e)}), 500
