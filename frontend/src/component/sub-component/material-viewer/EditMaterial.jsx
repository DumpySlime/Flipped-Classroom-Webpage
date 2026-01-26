import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import SlideExplanation from './slide-template/SlideExplanation';
import SlideExample from './slide-template/SlideExample';

function EditMaterial({ material, onClose }) {
    const [slides, setSlides] = useState(null);
    const [questions, setQuestions] = useState([]);
    const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
    const [err, setErr] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [materialId, setMaterialId] = useState(null);
    const [editMode, setEditMode] = useState(true);

    useEffect(() => {
        if (material) {
            loadMaterial();
        }
    }, [material]);

    const loadMaterial = async () => {
        try {
            setLoading(true);
            setErr(null);

            const response = await axios.get(`/db/material?material_id=${material?.id}`);
            const slidesData = response.data.materials[0]?.slides || [];
            const slidesArray = Array.isArray(slidesData) ? slidesData : slidesData?.slides || [];
            const normalizedSlides = slidesArray.map(slide => ({
                ...slide,
                slidetype: slide.slideType || slide.slidetype,
            }));
            setSlides(normalizedSlides);
            setCurrentSlideIndex(0);
            setMaterialId(material.id);

            const questionsResponse = await axios.get(`/db/question?material_id=${material.id}`);
            const questionsList = questionsResponse.data?.questions || [];
            setQuestions(questionsList);
        } catch (error) {
            console.error('Error loading material:', error);
            setErr('Failed to load material');
        } finally {
            setLoading(false);
        }
    };

    const handleSlideChange = (field, value) => {
        setSlides(prev => {
            const newSlides = [...prev];
            newSlides[currentSlideIndex] = {
                ...newSlides[currentSlideIndex],
                [field]: value
            };
            return newSlides;
        });
    };

    const handleQuestionChange = (qIndex, qSubIndex, field, value) => {
        setQuestions(prev => prev.map((group, gIndex) => {
            if (gIndex !== qIndex) return group;
            return {
                ...group,
                question_content: {
                    ...group.question_content,
                    questions: group.question_content.questions.map((question, qIndex) => {
                        if (qIndex !== qSubIndex) return question;
                        return {
                            ...question,
                            [field]: value
                        };
                    })
                }
            };
        }));
    };

    const handleOptionChange = (qIndex, qSubIndex, optIndex, value) => {
        setQuestions(prev => prev.map((group, gIndex) => {
            if (gIndex !== qIndex) return group;
            return {
                ...group,
                question_content: {
                    ...group.question_content,
                    questions: group.question_content.questions.map((question, qIndex) => {
                        if (qIndex !== qSubIndex) return question;
                        return {
                            ...question,
                            options: (question.options || []).map((option, oIndex) => {
                                if (oIndex !== optIndex) return option;
                                return value;
                            })
                        };
                    })
                }
            };
        }));
    };

    const handleAddOption = (qIndex, qSubIndex) => {
        setQuestions(prev => prev.map((group, gIndex) => {
            if (gIndex !== qIndex) return group;
            return {
                ...group,
                question_content: {
                    ...group.question_content,
                    questions: group.question_content.questions.map((question, qIndex) => {
                        if (qIndex !== qSubIndex) return question;
                        const options = question.options || [];
                        const newOption = `Option ${options.length + 1}`;
                        return {
                            ...question,
                            options: [...options, newOption]
                        };
                    })
                }
            };
        }));
    };

    const handleRemoveOption = (qIndex, qSubIndex, optIndex) => {
        setQuestions(prev => prev.map((group, gIndex) => {
            if (gIndex !== qIndex) return group;
            return {
                ...group,
                question_content: {
                    ...group.question_content,
                    questions: group.question_content.questions.map((question, qIndex) => {
                        if (qIndex !== qSubIndex) return question;
                        return {
                            ...question,
                            options: (question.options || []).filter((_, oIndex) => oIndex !== optIndex)
                        };
                    })
                }
            };
        }));
    };

    const handleAddQuestion = (qIndex) => {
        setQuestions(prev => prev.map((group, gIndex) => {
            if (gIndex !== qIndex) return group;
            return {
                ...group,
                question_content: {
                    ...group.question_content,
                    questions: [
                        ...(group.question_content.questions || []),
                        {
                            questionText: 'New Question',
                            questionType: 'multiple_choice',
                            options: ['Option A', 'Option B', 'Option C', 'Option D'],
                            correctAnswer: 0,
                            explanation: '',
                            learningObjective: ''
                        }
                    ]
                }
            };
        }));
    };

    const handleRemoveQuestion = (qIndex, qSubIndex) => {
        setQuestions(prev => prev.map((group, gIndex) => {
            if (gIndex !== qIndex) return group;
            const questionContent = group.question_content?.questions || [];
            if (questionContent.length <= 1) {
                alert('Cannot remove the last question');
                return group;
            }
            return {
                ...group,
                question_content: {
                    ...group.question_content,
                    questions: questionContent.filter((_, qIndex) => qIndex !== qSubIndex)
                }
            };
        }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setErr(null);

            const materialResponse = await axios.put(`/db/material-update?material_id=${material.id}`, {
                slides: slides
            });

            for (const q of questions) {
                const qId = q.id || (q._id && (q._id.$oid || q._id));
                if (qId) {
                    await axios.put(`/db/question-update?question_id=${qId}`, {
                        question_content: q.question_content
                    });
                }
            }

            console.log('Material and questions updated successfully');
            alert('Material updated successfully!');
            onClose();
        } catch (error) {
            console.error('Error updating material:', error);
            setErr('Failed to update material. Please try again.');
            alert('Failed to update material. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    if (err) return (
        <div style={{ padding: '20px', color: 'red' }}>
            <p>{err}</p>
            <button type="button" className="button primary" onClick={onClose}>Close</button>
        </div>
    );

    if (!slides || slides.length === 0) return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
            <p>Loading slides...</p>
        </div>
    );

    const totalSlides = slides.length;
    const currentSlide = slides[currentSlideIndex];

    const handleNextSlide = () => {
        if (currentSlideIndex < totalSlides - 1) {
            setCurrentSlideIndex(prev => prev + 1);
        }
    };

    const handlePrevSlide = () => {
        if (currentSlideIndex > 0) {
            setCurrentSlideIndex(prev => prev - 1);
        }
    };

    const progressPercentage = totalSlides > 0 ? ((currentSlideIndex + 1) / totalSlides) * 100 : 0;

    const renderSlide = () => {
        if (!currentSlide) return null;
        if (currentSlide.slidetype === 'explanation') {
            return <SlideExplanation slide={currentSlide} />;
        }
        if (currentSlide.slidetype === 'example') {
            return <SlideExample slide={currentSlide} />;
        }
        return <div>Unknown slide type</div>;
    };

    const renderEditableSlide = () => {
        if (!currentSlide) return null;

        const contentArray = Array.isArray(currentSlide.content) ? currentSlide.content : [currentSlide.content];
        const question = contentArray[0] || '';
        const solutionSteps = contentArray.slice(1).join('\n');

        return (
            <div style={{ padding: '20px' }}>
                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                        Subtitle:
                    </label>
                    <input
                        type="text"
                        value={currentSlide.subtitle || ''}
                        onChange={(e) => handleSlideChange('subtitle', e.target.value)}
                        style={{
                            width: '100%',
                            padding: '10px',
                            border: '1px solid #ddd',
                            borderRadius: '5px'
                        }}
                    />
                </div>

                {currentSlide.slidetype === 'example' ? (
                    <>
                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Question:
                            </label>
                            <textarea
                                value={question}
                                onChange={(e) => {
                                    const newContent = [e.target.value, ...contentArray.slice(1)];
                                    handleSlideChange('content', newContent);
                                }}
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    border: '1px solid #ddd',
                                    borderRadius: '5px',
                                    minHeight: '80px',
                                    resize: 'vertical'
                                }}
                            />
                        </div>

                        <div style={{ marginBottom: '15px' }}>
                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                Solution:
                            </label>
                            <textarea
                                value={solutionSteps}
                                onChange={(e) => {
                                    const newContent = [contentArray[0], ...e.target.value.split('\n')];
                                    handleSlideChange('content', newContent);
                                }}
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    border: '1px solid #ddd',
                                    borderRadius: '5px',
                                    minHeight: '200px',
                                    resize: 'vertical'
                                }}
                            />
                        </div>
                    </>
                ) : (
                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                            Content:
                        </label>
                        <textarea
                            value={currentSlide.content || ''}
                            onChange={(e) => handleSlideChange('content', e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px',
                                border: '1px solid #ddd',
                                borderRadius: '5px',
                                minHeight: '200px',
                                resize: 'vertical'
                            }}
                        />
                    </div>
                )}
            </div>
        );
    };

    const renderQuestionPreview = () => {
        return (
            <div>
                {questions.map((q, index) => {
                    const questionContent = q.question_content?.questions || [];
                    return (
                        <div key={index} style={{
                            backgroundColor: '#f9f9f9',
                            padding: '20px',
                            marginBottom: '20px',
                            borderRadius: '8px',
                            border: '1px solid #e0e0e0'
                        }}>
                            <p style={{
                                marginBottom: '20px',
                                fontWeight: 'bold',
                                color: '#4CAF50',
                                fontSize: '16px'
                            }}>
                                ✓ Question Group {index + 1}
                            </p>

                            {questionContent.map((question, qIndex) => {
                                const questionKey = `${index}-${qIndex}`;

                                return (
                                    <div key={qIndex} style={{
                                        backgroundColor: 'white',
                                        padding: '20px',
                                        marginBottom: '20px',
                                        borderRadius: '8px',
                                        border: '1px solid #ddd'
                                    }}>
                                        <div style={{
                                            fontWeight: 'bold',
                                            marginBottom: '15px',
                                            fontSize: '16px',
                                            color: '#333'
                                        }}>
                                            Question {qIndex + 1}: {question.questionText}
                                        </div>

                                        {question.questionType === 'multiple_choice' && question.options ? (
                                            <div style={{ paddingLeft: '20px' }}>
                                                {question.options.map((option, optIndex) => {
                                                    const optionLetter = String.fromCharCode(65 + optIndex);
                                                    const isOptionCorrect = question.correctAnswer === optIndex;

                                                    let optionStyle = {
                                                        marginBottom: '8px',
                                                        padding: '12px',
                                                        backgroundColor: 'white',
                                                        borderRadius: '4px',
                                                        border: '2px solid #ddd',
                                                        transition: 'all 0.2s ease'
                                                    };

                                                    if (isOptionCorrect) {
                                                        optionStyle.backgroundColor = '#e8f5e9';
                                                        optionStyle.borderColor = '#4CAF50';
                                                        optionStyle.color = '#2e7d32';
                                                    }

                                                    return (
                                                        <div key={optIndex} style={optionStyle}>
                                                            <strong>{optionLetter}.</strong> {option}
                                                            {isOptionCorrect && (
                                                                <span style={{ marginLeft: '10px', color: '#4CAF50' }}>✓</span>
                                                            )}
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        ) : (
                                            <div style={{ marginTop: '10px', paddingLeft: '20px' }}>
                                                <div style={{
                                                    padding: '15px',
                                                    backgroundColor: '#f5f5f5',
                                                    borderRadius: '4px',
                                                    border: '1px solid #ddd',
                                                    fontSize: '14px'
                                                }}>
                                                    {question.correctAnswer || 'No correct answer set'}
                                                </div>
                                            </div>
                                        )}

                                        {question.explanation && (
                                            <div style={{
                                                marginTop: '15px',
                                                padding: '15px',
                                                backgroundColor: '#fff3e0',
                                                borderRadius: '5px',
                                                borderLeft: '5px solid #ff9800',
                                                fontSize: '14px'
                                            }}>
                                                <strong>📝 Explanation:</strong> {question.explanation}
                                            </div>
                                        )}

                                        {question.learningObjective && (
                                            <div style={{
                                                marginTop: '15px',
                                                padding: '10px',
                                                backgroundColor: '#e3f2fd',
                                                borderRadius: '5px',
                                                fontSize: '14px',
                                                color: '#1976d2'
                                            }}>
                                                <strong>💡 Learning Objective:</strong> {question.learningObjective}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '20px'
            }}>
                <h2 style={{ margin: 0 }}>Edit Material</h2>
                <div style={{ display: 'flex', gap: '10px' }}>
                    <button
                        type="button"
                        className="button subtle"
                        onClick={() => setEditMode(!editMode)}
                    >
                        {editMode ? 'Preview Mode' : 'Edit Mode'}
                    </button>
                    <button
                        type="button"
                        className="button primary"
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button type="button" className="button subtle" onClick={onClose}>Close</button>
                </div>
            </div>

            <div style={{
                backgroundColor: 'white',
                borderRadius: '10px',
                boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                marginBottom: '30px',
                overflow: 'hidden'
            }}>
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '15px 20px',
                    backgroundColor: '#f5f5f5',
                    borderBottom: '2px solid #ddd'
                }}>
                    <button
                        type="button"
                        onClick={handlePrevSlide}
                        disabled={currentSlideIndex === 0}
                        style={{
                            padding: '10px 20px',
                            fontSize: '16px',
                            backgroundColor: currentSlideIndex === 0 ? '#ccc' : '#4CAF50',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: currentSlideIndex === 0 ? 'not-allowed' : 'pointer',
                            fontWeight: 'bold'
                        }}
                    >
                        ← Previous
                    </button>

                    <div style={{ fontSize: '16px', fontWeight: 'bold' }}>
                        Slide {currentSlideIndex + 1} of {totalSlides}
                    </div>

                    <button
                        type="button"
                        onClick={handleNextSlide}
                        disabled={currentSlideIndex === totalSlides - 1}
                        style={{
                            padding: '10px 20px',
                            fontSize: '16px',
                            backgroundColor: currentSlideIndex === totalSlides - 1 ? '#ccc' : '#4CAF50',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: currentSlideIndex === totalSlides - 1 ? 'not-allowed' : 'pointer',
                            fontWeight: 'bold'
                        }}
                    >
                        Next →
                    </button>
                </div>

                <div style={{
                    position: 'relative',
                    minHeight: '400px',
                    backgroundColor: 'white'
                }}>
                    <div
                        onClick={handlePrevSlide}
                        style={{
                            position: 'absolute',
                            left: 0,
                            top: 0,
                            bottom: 0,
                            width: '15%',
                            cursor: currentSlideIndex > 0 ? 'pointer' : 'default',
                            zIndex: 10
                        }}
                    ></div>

                    <div style={{ padding: '40px 60px' }}>
                        {editMode ? renderEditableSlide() : renderSlide()}
                    </div>

                    <div
                        onClick={handleNextSlide}
                        style={{
                            position: 'absolute',
                            right: 0,
                            top: 0,
                            bottom: 0,
                            width: '15%',
                            cursor: currentSlideIndex < totalSlides - 1 ? 'pointer' : 'default',
                            zIndex: 10
                        }}
                    ></div>
                </div>

                <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: '#e0e0e0',
                    overflow: 'hidden'
                }}>
                    <div
                        style={{
                            width: `${progressPercentage}%`,
                            height: '100%',
                            backgroundColor: '#4CAF50',
                            transition: 'width 0.3s ease'
                        }}
                    ></div>
                </div>

                <div style={{
                    display: 'flex',
                    gap: '10px',
                    padding: '15px',
                    overflowX: 'auto',
                    backgroundColor: '#f9f9f9'
                }}>
                    {slides.map((slide, index) => (
                        <div
                            key={index}
                            onClick={() => setCurrentSlideIndex(index)}
                            style={{
                                minWidth: '80px',
                                padding: '10px',
                                border: index === currentSlideIndex ? '3px solid #4CAF50' : '2px solid #ddd',
                                borderRadius: '5px',
                                cursor: 'pointer',
                                backgroundColor: index === currentSlideIndex ? '#e8f5e9' : 'white',
                                textAlign: 'center',
                                transition: 'all 0.2s ease'
                            }}
                        >
                            <div style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '5px' }}>
                                {index + 1}
                            </div>
                            <div style={{ fontSize: '12px', color: '#666' }}>
                                {slide.subtitle}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div
                style={{
                    backgroundColor: 'white',
                    borderRadius: '10px',
                    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                    padding: '30px',
                    marginTop: '30px'
                }}
            >
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '20px',
                    borderBottom: '3px solid #4CAF50',
                    paddingBottom: '10px'
                }}>
                    <h2 style={{
                        fontSize: '24px',
                        fontWeight: 'bold',
                        margin: 0
                    }}>
                        📝 Questions
                    </h2>
                </div>

                {questions.length > 0 ? (
                    <div>
                        <p style={{
                            marginBottom: '20px',
                            fontWeight: 'bold',
                            color: '#4CAF50',
                            fontSize: '16px'
                        }}>
                            ✓ {questions.length} question(s) available
                        </p>

                        {editMode ? (
                            <div>
                                {questions.map((q, index) => {
                                    const questionContent = q.question_content?.questions || [];
                                    return (
                                        <div key={index} style={{
                                            backgroundColor: '#f9f9f9',
                                            padding: '20px',
                                            marginBottom: '20px',
                                            borderRadius: '8px',
                                            border: '1px solid #e0e0e0'
                                        }}>
                                            <div style={{
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'center',
                                                marginBottom: '15px'
                                            }}>
                                                <h3 style={{ margin: 0 }}>Question Group {index + 1}</h3>
                                                <button
                                                    type="button"
                                                    className="button primary"
                                                    onClick={() => handleAddQuestion(index)}
                                                    style={{ padding: '5px 10px', fontSize: '14px' }}
                                                >
                                                    + Add Question
                                                </button>
                                            </div>

                                            {questionContent.map((question, qIndex) => (
                                                <div key={qIndex} style={{
                                                    backgroundColor: 'white',
                                                    padding: '20px',
                                                    marginBottom: '20px',
                                                    borderRadius: '8px',
                                                    border: '1px solid #ddd'
                                                }}>
                                                    <div style={{
                                                        display: 'flex',
                                                        justifyContent: 'space-between',
                                                        alignItems: 'center',
                                                        marginBottom: '15px'
                                                    }}>
                                                        <h4 style={{ margin: 0 }}>Question {qIndex + 1}</h4>
                                                        <button
                                                            type="button"
                                                            className="button danger subtle"
                                                            onClick={() => handleRemoveQuestion(index, qIndex)}
                                                            style={{ padding: '5px 10px', fontSize: '12px' }}
                                                        >
                                                            Remove
                                                        </button>
                                                    </div>

                                                    <div style={{ marginBottom: '15px' }}>
                                                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                                            Question Text:
                                                        </label>
                                                        <textarea
                                                            value={question.questionText || ''}
                                                            onChange={(e) => handleQuestionChange(index, qIndex, 'questionText', e.target.value)}
                                                            style={{
                                                                width: '100%',
                                                                padding: '10px',
                                                                border: '1px solid #ddd',
                                                                borderRadius: '5px',
                                                                minHeight: '80px',
                                                                resize: 'vertical'
                                                            }}
                                                        />
                                                    </div>

                                                    {(question.options && question.options.length > 0) && (
                                                        <div style={{ marginBottom: '15px' }}>
                                                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                                                Options:
                                                                <span style={{ fontSize: '12px', fontWeight: 'normal', color: '#666', marginLeft: '10px' }}>
                                                                    (Select the radio button on the left to set the correct answer)
                                                                </span>
                                                            </label>
                                                            {(question.options || []).map((option, optIndex) => (
                                                                <div key={optIndex} style={{
                                                                    display: 'flex',
                                                                    gap: '10px',
                                                                    marginBottom: '10px',
                                                                    alignItems: 'center'
                                                                }}>
                                                                    <input
                                                                        type="radio"
                                                                        name={`correct-${index}-${qIndex}`}
                                                                        checked={question.correctAnswer === optIndex}
                                                                        onChange={() => handleQuestionChange(index, qIndex, 'correctAnswer', optIndex)}
                                                                        style={{ cursor: 'pointer' }}
                                                                    />
                                                                    <input
                                                                        type="text"
                                                                        value={option}
                                                                        onChange={(e) => handleOptionChange(index, qIndex, optIndex, e.target.value)}
                                                                        style={{
                                                                            flex: 1,
                                                                            padding: '8px',
                                                                            border: '1px solid #ddd',
                                                                            borderRadius: '5px'
                                                                        }}
                                                                    />
                                                                    <button
                                                                        type="button"
                                                                        className="button danger subtle"
                                                                        onClick={() => handleRemoveOption(index, qIndex, optIndex)}
                                                                        style={{ padding: '5px 10px', fontSize: '12px' }}
                                                                    >
                                                                        Remove
                                                                    </button>
                                                                </div>
                                                            ))}
                                                            <button
                                                                type="button"
                                                                className="button primary"
                                                                onClick={() => handleAddOption(index, qIndex)}
                                                                style={{ padding: '5px 10px', fontSize: '14px' }}
                                                            >
                                                                + Add Option
                                                            </button>
                                                        </div>
                                                    )}

                                                    {(!question.options || question.options.length === 0) && (
                                                        <div style={{ marginBottom: '15px' }}>
                                                            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                                                Correct Answer:
                                                            </label>
                                                            <textarea
                                                                value={question.correctAnswer || ''}
                                                                onChange={(e) => handleQuestionChange(index, qIndex, 'correctAnswer', e.target.value)}
                                                                style={{
                                                                    width: '100%',
                                                                    padding: '10px',
                                                                    border: '1px solid #ddd',
                                                                    borderRadius: '5px',
                                                                    minHeight: '80px',
                                                                    resize: 'vertical'
                                                                }}
                                                            />
                                                        </div>
                                                    )}

                                                    <div style={{ marginBottom: '15px' }}>
                                                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                                            Explanation:
                                                        </label>
                                                        <textarea
                                                            value={question.explanation || ''}
                                                            onChange={(e) => handleQuestionChange(index, qIndex, 'explanation', e.target.value)}
                                                            style={{
                                                                width: '100%',
                                                                padding: '10px',
                                                                border: '1px solid #ddd',
                                                                borderRadius: '5px',
                                                                minHeight: '80px',
                                                                resize: 'vertical'
                                                            }}
                                                        />
                                                    </div>

                                                    <div style={{ marginBottom: '15px' }}>
                                                        <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                                                            Learning Objective:
                                                        </label>
                                                        <input
                                                            type="text"
                                                            value={question.learningObjective || ''}
                                                            onChange={(e) => handleQuestionChange(index, qIndex, 'learningObjective', e.target.value)}
                                                            style={{
                                                                width: '100%',
                                                                padding: '10px',
                                                                border: '1px solid #ddd',
                                                                borderRadius: '5px'
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            renderQuestionPreview()
                        )}
                    </div>
                ) : (
                    <div style={{
                        textAlign: 'center',
                        padding: '40px',
                        color: '#999',
                        fontSize: '16px'
                    }}>
                        <p>⏳ No questions available yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default EditMaterial;
