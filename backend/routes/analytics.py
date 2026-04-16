from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime

analytics_bp = Blueprint('analytics', __name__)

db = None

def init_analytics(database):
    """Initialize the analytics blueprint with database connection"""
    global db
    db = database
    # Auto-create index on ai_reports for fast student lookup
    db.ai_reports.create_index([("student_id", 1)], unique=True)
    print("[ANALYTICS] Analytics module initialized")


@analytics_bp.route('/api/analytics/students', methods=['GET'])
@jwt_required()
def get_student_analytics():
    try:
        total_materials_count = db.materials.count_documents({"is_deleted": {"$ne": True}})
        if total_materials_count == 0:
            total_materials_count = 1

        pipeline = [
            {"$match": {"status": "submitted"}},

            # ✅ 加 lookup 排除已刪除 material 的 submission
            {
                "$lookup": {
                    "from": "materials",
                    "localField": "material_id",
                    "foreignField": "_id",
                    "as": "material_info"
                }
            },
            # ✅ 過濾：只保留 material 未刪除的 submissions
            {
                "$match": {
                    "material_info": {"$ne": []},                    # material 存在
                    "material_info.0.is_deleted": {"$ne": True}      # 且未刪除
                }
            },

            {
                "$group": {
                    "_id": "$student_id",
                    "total_submissions": {"$sum": 1},
                    "avg_score": {"$avg": "$total_score"},           # ← 現在只計未刪除 material
                    "last_activity": {"$max": "$submission_time"},
                    "materials_attempted": {"$addToSet": "$material_id"}
                }
            },
            {
                "$lookup": {
                    "from": "students",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "student_info"
                }
            },
            {"$unwind": {"path": "$student_info", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
            # ✅ 加入 lookup materials 過濾已刪除
            {
                "$lookup": {
                    "from": "materials",
                    "let": {"attempted": "$materials_attempted"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {"$in": ["$_id", "$$attempted"]},
                                "is_deleted": {"$ne": True}   # ← 只計未刪除
                            }
                        },
                        {"$project": {"_id": 1}}
                    ],
                    "as": "valid_materials_attempted"
                }
            },
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "name": {
                        "$ifNull": [
                            "$student_info.name",
                            {"$ifNull": ["$user_info.username", "Unknown Student"]}
                        ]
                    },
                    # ✅ 用 valid_materials_attempted（已過濾刪除）計 progress
                    "progress": {
                        "$min": [   # ← cap 至 100%
                            100,
                            {
                                "$round": [
                                    {
                                        "$multiply": [
                                            {"$divide": [
                                                {"$size": "$valid_materials_attempted"},
                                                total_materials_count
                                            ]},
                                            100
                                        ]
                                    },
                                    0
                                ]
                            }
                        ]
                    },
                    "avgQuizScore": {"$round": ["$avg_score", 0]},
                    "lastActivity": "$last_activity",
                    "totalSubmissions": "$total_submissions"
                }
            },
            {"$sort": {"lastActivity": -1}}
        ]

        results = list(db.student_answers.aggregate(pipeline))
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
    Generate AI report for a single student, save both EN + ZH to ai_reports collection
    """
    try:
        data = request.get_json()
        student_id_str = data.get('student_id')

        if not student_id_str:
            return jsonify({"error": "student_id is required"}), 400

        try:
            student_id = ObjectId(student_id_str)
        except:
            return jsonify({"error": "Invalid student_id format"}), 400

        student = db.students.find_one({"_id": student_id})
        if not student:
            student = db.users.find_one({"_id": student_id})
        if not student:
            return jsonify({"error": "Student not found"}), 404

        student_name = student.get('name') or student.get('username', 'Student')

        submissions = list(db.student_answers.find({
            "student_id": student_id,
            "status": "submitted"
        }).sort("submission_time", -1))

        if not submissions:
            no_data_en = f"## No Data Available\n\n{student_name} has not completed any quizzes or assignments yet."
            no_data_zh = f"## 暫無資料\n\n{student_name} 尚未完成任何測驗或作業。"
            return jsonify({"report_en": no_data_en, "report_zh": no_data_zh}), 200

        analytics_data = calculate_student_statistics_with_questions(submissions, student_name)

        from routes.ai import generate_performance_report, translate_report_to_chinese

        report_en = generate_performance_report(analytics_data)
        report_zh = translate_report_to_chinese(report_en)

        db.ai_reports.update_one(
            {"student_id": student_id},
            {"$set": {
                "student_id": student_id,
                "student_name": student_name,
                "report_en": report_en,
                "report_zh": report_zh,
                "generated_at": datetime.utcnow(),
                "generated_by": ObjectId(get_jwt_identity())
            }},
            upsert=True
        )

        return jsonify({"report_en": report_en, "report_zh": report_zh}), 200

    except Exception as e:
        print(f"Error in generate_ai_report: {str(e)}")
        return jsonify({"error": "Failed to generate report", "details": str(e)}), 500


@analytics_bp.route('/api/analytics/report/all', methods=['POST'])
@jwt_required()
def generate_all_reports():
    """
    Generate and store AI reports for ALL students in one go
    """
    try:
        from routes.ai import generate_performance_report, translate_report_to_chinese

        students = list(db.student_answers.aggregate([
            {"$match": {"status": "submitted"}},
            {"$group": {"_id": "$student_id"}}
        ]))

        results = {"success": [], "failed": []}

        for s in students:
            try:
                student_id = s["_id"]
                student = db.students.find_one({"_id": student_id}) or db.users.find_one({"_id": student_id})
                student_name = (student.get('name') or student.get('username', 'Student')) if student else 'Unknown'

                submissions = list(db.student_answers.find({
                    "student_id": student_id,
                    "status": "submitted"
                }).sort("submission_time", -1))

                if not submissions:
                    results["failed"].append({"id": str(student_id), "error": "No submissions"})
                    continue

                analytics_data = calculate_student_statistics_with_questions(submissions, student_name)
                report_en = generate_performance_report(analytics_data)
                report_zh = translate_report_to_chinese(report_en)

                db.ai_reports.update_one(
                    {"student_id": student_id},
                    {"$set": {
                        "student_id": student_id,
                        "student_name": student_name,
                        "report_en": report_en,
                        "report_zh": report_zh,
                        "generated_at": datetime.utcnow(),
                        "generated_by": ObjectId(get_jwt_identity())
                    }},
                    upsert=True
                )
                results["success"].append(str(student_id))

            except Exception as e:
                results["failed"].append({"id": str(s["_id"]), "error": str(e)})

        return jsonify(results), 200

    except Exception as e:
        print(f"Error in generate_all_reports: {str(e)}")
        return jsonify({"error": "Failed to generate all reports", "details": str(e)}), 500


@analytics_bp.route('/api/analytics/report/<student_id>', methods=['GET'])
@jwt_required()
def get_stored_report(student_id):
    """
    Fetch previously stored AI report for a student from ai_reports collection
    """
    try:
        report = db.ai_reports.find_one({"student_id": ObjectId(student_id)})
        if not report:
            return jsonify({"error": "No report found"}), 404

        generated_at = report.get("generated_at")
        return jsonify({
            "report_en": report.get("report_en"),
            "report_zh": report.get("report_zh"),
            "generated_at": generated_at.isoformat() if generated_at else None
        }), 200

    except Exception as e:
        print(f"Error in get_stored_report: {str(e)}")
        return jsonify({"error": "Failed to fetch report", "details": str(e)}), 500


def calculate_student_statistics_with_questions(submissions, student_name):
    
    # ✅ 先取得所有未刪除 material 的 ID set
    valid_material_ids = set(
        str(m["_id"]) for m in db.materials.find(
            {"is_deleted": {"$ne": True}},
            {"_id": 1}
        )
    )

    # ✅ 只保留 submission 屬於未刪除 material 的
    valid_submissions = [
        s for s in submissions
        if str(s.get('material_id')) in valid_material_ids
    ]

    total_submissions = len(valid_submissions)

    # ✅ scores 只計 valid submissions
    scores = [s.get('total_score', 0) for s in valid_submissions]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0

    materials_attempted = set(str(s.get('material_id')) for s in valid_submissions)

    total_materials = db.materials.count_documents({"is_deleted": {"$ne": True}})

    # ✅ 只計 materials_attempted 入面未被刪除的
    valid_attempted_ids = [ObjectId(mid) for mid in materials_attempted if mid]
    valid_attempted_count = db.materials.count_documents({
        "_id": {"$in": valid_attempted_ids},
        "is_deleted": {"$ne": True}
    })

    progress_percentage = min(
        100,  # ← cap 至 100%
        (valid_attempted_count / total_materials * 100) if total_materials > 0 else 0
    )

    # ✅ incorrect questions 也只從 valid submissions 計
    incorrect_questions = []
    correct_count = 0
    total_questions = 0

    for submission in valid_submissions:   # ← 改用 valid_submissions
        answers = submission.get('answers', [])
        material_id = submission.get('material_id')

        for answer in answers:
            total_questions += 1
            is_correct = answer.get('is_correct', False)

            if is_correct:
                correct_count += 1
            else:
                question_id = answer.get('question_id', '')
                question_doc = db.questions.find_one({"material_id": material_id})

                if question_doc:
                    question_content = question_doc.get('question_content', {})
                    questions_list = question_content.get('questions', [])
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

    recent_submissions = valid_submissions[:5]   # ← 改用 valid_submissions
    recent_performance = [
        {
            "score": s.get('total_score', 0),
            "date": s.get('submission_time', ''),
            "questions": len(s.get('answers', []))
        }
        for s in recent_submissions
    ]

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

    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0

    return {
        "student_name": student_name,
        "total_submissions": total_submissions,
        "avg_score": avg_score,
        "max_score": max_score,
        "min_score": min_score,
        "progress_percentage": progress_percentage,          # ← 已修正
        "materials_completed": valid_attempted_count,        # ← 用 valid count
        "total_materials": total_materials,
        "trend": trend,
        "recent_performance": recent_performance,
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_count": total_questions - correct_count,
        "accuracy": accuracy,
        "incorrect_questions": incorrect_questions[:10]
    }


@analytics_bp.route('/api/analytics/student/<student_id>', methods=['GET'])
@jwt_required()
def get_student_detail(student_id):
    try:
        student_obj_id = ObjectId(student_id)
        submissions = list(db.student_answers.find({
            "student_id": student_obj_id
        }).sort("submission_time", -1))

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