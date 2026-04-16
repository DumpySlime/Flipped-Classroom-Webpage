import { useState, useEffect, useCallback } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import { apiRequest, studentAnswerAPI } from '../../../services/api';

function ViewQuestion({ materialId, userRole, onEditQuestion }) {
    const [questions, setQuestions] = useState([]);
    const [topic, setTopic] = useState("");
    const [userAnswers, setUserAnswers] = useState({});
    const [submitted, setSubmitted] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [score, setScore] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [questionRefreshKey, setQuestionRefreshKey] = useState(0);

    const refreshQuestions = useCallback(() => {
        setQuestionRefreshKey(k => k + 1);
    }, []);

    useEffect(() => {
        if (!materialId) return;
        setLoading(true);
        setError(null);

        apiRequest(`/db/question?material_id=${materialId}`)
            .then(data => {
                if (!data.questions || data.questions.length === 0) {
                    setQuestions([]);
                    setTopic("");
                    return;
                }

                const fetchedQuestion = data.questions[0];
                const parsed = typeof fetchedQuestion.question_content === 'string'
                    ? JSON.parse(fetchedQuestion.question_content)
                    : fetchedQuestion.question_content;

                setQuestions(parsed.questions || []);
                setTopic(parsed.topic || "");
            })
            .catch(e => {
                console.error("Error fetching questions:", e);
                setError("Unable to load questions: " + e.message);
            })
            .finally(() => setLoading(false));
    }, [materialId, questionRefreshKey]);

    const handleAnswerChange = (index, value) => {
        setUserAnswers(prev => ({
            ...prev,
            [`0-${index}`]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);

        const studentId = sessionStorage.getItem('user_id');

        const formattedAnswers = questions.map((q, index) => {
            const questionKey = `0-${index}`;
            const userAnswer = userAnswers[questionKey];

            let isCorrect = false;
            if (q.questionType === 'multiple_choice') {
                isCorrect = q.correctAnswer === userAnswer;
            }

            return {
                question_id: `${materialId}-q-${index}`,
                user_answer: userAnswer ?? "",
                is_correct: isCorrect,
                score: isCorrect ? (q.score || 10) : 0,
            };
        });

        const totalScore = formattedAnswers.reduce((sum, a) => sum + a.score, 0);
        const maxScore = questions.length * 10;
        const pct = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0;

        try {
            await studentAnswerAPI.submit({
                student_id: studentId,
                material_id: materialId,
                answers: formattedAnswers,
                total_score: totalScore,
                status: 'submitted'
            });
            setScore(pct);
            setSubmitted(true);
        } catch (err) {
            setError('Failed to submit answers: ' + err.message);
        } finally {
            setSubmitting(false);
        }
    };


    if (loading) return (
        <div className="question-viewer">
            <p>Loading questions...</p>
        </div>
    );

    if (submitted) return (
        <div className="question-viewer">
            <div className="score-display">
                <h2>{score}%</h2>
                <p>You got {score}% of the questions correct!</p>
            </div>
            <button onClick={() => { setSubmitted(false); setUserAnswers({}); }}>
                Try Again
            </button>
        </div>
    );

    return (
        <div className="question-viewer">
            <div className="question-header">
                <h3>Questions for Topic: {topic}</h3>
                {(userRole === 'teacher' || userRole === 'admin') && onEditQuestion && (
                    <button
                        className="edit-btn"
                        onClick={() => onEditQuestion(refreshQuestions)}
                    >
                        Edit Questions
                    </button>
                )}
            </div>

            {error && <p style={{ color: 'red' }}>{error}</p>}

            {questions.length === 0 ? (
                <p>⏳ No questions available.</p>
            ) : (
                <form onSubmit={handleSubmit}>
                    {questions.map((q, index) => {
                        const questionKey = `0-${index}`;
                        const selectedOption = userAnswers[questionKey];

                        return (
                            <div className="question-item" key={index}>
                                <p><strong>Q{index + 1}:</strong> {q.questionText}</p>

                                {q.questionType === 'multiple_choice' ? (
                                    <div className="options">
                                        {q.options.map((option, optIndex) => (
                                            <label key={optIndex} style={{ display: 'block', marginBottom: '8px' }}>
                                                <input
                                                    type="radio"
                                                    name={`question-${index}`}
                                                    value={optIndex}
                                                    checked={selectedOption === optIndex}
                                                    onChange={() => handleAnswerChange(index, optIndex)}
                                                />
                                                {String.fromCharCode(65 + optIndex)}. {option}
                                            </label>
                                        ))}
                                    </div>
                                ) : (
                                    <textarea
                                        className="short-answer"
                                        placeholder="Enter your answer here..."
                                        value={userAnswers[questionKey] || ''}
                                        onChange={(e) => handleAnswerChange(index, e.target.value)}
                                        rows={4}
                                        style={{ width: '100%', padding: '8px' }}
                                    />
                                )}
                            </div>
                        );
                    })}

                    <button
                        type="submit"
                        disabled={submitting}
                        style={{ marginTop: '20px', padding: '10px 20px' }}
                    >
                        {submitting ? 'Submitting...' : 'Submit Answers'}
                    </button>
                </form>
            )}
        </div>
    );
}

export default ViewQuestion;