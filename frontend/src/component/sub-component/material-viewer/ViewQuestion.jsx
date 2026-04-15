import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import { apiRequest, studentAnswerAPI } from '../../../services/api'; 

function ViewQuestion ({ materialId }) {
    const [error, setError] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [topic, setTopic] = useState("");
    const [answers, setAnswers] = useState({});

    useEffect(() => {
        apiRequest(`/db/question?material_id=${materialId}`)
        .then(data => {
            if (!data.questions || data.questions.length === 0) {
                setError("No questions found for this material.");
                return;
            }

            const fetchedQuestion = data.questions[0];

            const parsed = JSON.parse(fetchedQuestion.question_content);

            setQuestions(parsed.questions || []);
            setTopic(parsed.topic || "");
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
const handleSubmit = async (e) => {
  e.preventDefault();
  
  const studentId = sessionStorage.getItem('user_id');
  
  const formattedAnswers = Object.entries(answers).map(([index, value]) => ({
    question_id: `${materialId}-q-${index}`,
    user_answer: value,
  }));

  try {
    await studentAnswerAPI.submit({
      student_id: studentId,
      material_id: materialId,
      answers: formattedAnswers,
      status: 'submitted'
    });
    alert('Answers submitted successfully!');
  } catch (err) {
    setError('Failed to submit answers: ' + err.message);
  }
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