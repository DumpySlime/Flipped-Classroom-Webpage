import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios'

function ViewQuestion ({ materialId }) {
    const [error, setError] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [topic, setTopic] = useState("");
    const [answers, setAnswers] = useState({});

    useEffect(() => {
        axios.get(`/db/question?material_id=${materialId}`)
        .then(response => {
            console.log("Questions fetched:", response.data);
            const fetchedQuestions = response.data.questions;
            setQuestions(fetchedQuestions.question_content.questions);
            setTopic(fetchedQuestions.topic);
        })
        .catch(e => {
            console.log("Error fetching questions:", e);
            setError("Unable to load questions: " + e.message);
        });
    }, [materialId]);

    const handleAnswerChange = (questionIndex, value) => {
        setAnswers(prev => ({
            ...prev,
            [questionIndex]: value
        }));
    };

    // Submission logic
    const handleSubmit = (e) => {
        e.preventDefault();
        console.log("Submitted answers:", answers);
    };

    return (
        <div className="question-viewer">
            <h3>Questions for Topic: {topic}</h3>
            {questions.length === 0 ? (
                <p>No questions available.</p>
            ) : (
                <form onSubmit={handleSubmit}>
                    {questions.map((q, index) => (
                        <div className="question-item" key={index}>
                            <p><strong>Q{index + 1}:</strong> {q.questionText}</p>
                            
                            {q.questionType === "multiple_choice" ? (
                                <div className="options">
                                    {q.options.map((option, optIndex) => (
                                        <label key={optIndex} style={{ display: 'block', marginBottom: '8px' }}>
                                            <input
                                                type="radio"
                                                name={`question-${index}`}
                                                value={optIndex}
                                                checked={answers[index] === optIndex}
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
                                    value={answers[index] || ''}
                                    onChange={(e) => handleAnswerChange(index, e.target.value)}
                                    rows={4}
                                    style={{ width: '100%', padding: '8px' }}
                                />
                            )}
                        </div>
                    ))}
                    
                    <button type="submit" style={{ marginTop: '20px', padding: '10px 20px' }}>
                        Submit Answers
                    </button>
                </form>
            )}
        </div>
    );
}

export default ViewQuestion;