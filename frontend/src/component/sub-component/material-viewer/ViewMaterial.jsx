import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import SlideExplanation from './slide-template/SlideExplanation';
import SlideExample from './slide-template/SlideExample';

import EditMaterial from './EditMaterial';

function ViewMaterial({ material, materialData, userInfo, userRole, onClose}) {
	const [slides, setSlides] = useState(null);
	const [questions, setQuestions] = useState([]);
	const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
	const [err, setErr] = useState(null);
	const [loadingQuestions, setLoadingQuestions] = useState(true);
	const [userAnswers, setUserAnswers] = useState({});
	const [submitted, setSubmitted] = useState(false);
	const [score, setScore] = useState(0);
	const [materialId, setMaterialId] = useState(null);
	const [submitting, setSubmitting] = useState(false);
	const [savedSubmissionTime, setSavedSubmissionTime] = useState(null);
	
    const [showEdit, setShowEdit] = useState(false);
	const [selectedMaterial, setSelectedMaterial] = useState(null);

	// back navigation
	function handleBackToMaterials() {
        // Reset all state before navigating back
        setSlides(null);
        setQuestions([]);
        setCurrentSlideIndex(0);
        setErr(null);
        setLoadingQuestions(true);
        setUserAnswers({});
        setSubmitted(false);
        setScore(0);
        setMaterialId(null);
        setSavedSubmissionTime(null);
        
        // Call the onClose callback to return to MaterialList
        onClose();
    }

    function handleEditMaterial(materialToEdit) {
        setSelectedMaterial(materialToEdit);
        setShowEdit(true);
    } 

	// load saved submission (single submission expected)
	const loadStudentSubmission = async (studentId, materialIdParam, questionsList) => {
		if (!studentId || !materialIdParam || !questionsList || questionsList.length === 0) return;

		try {
		const resp = await axios.get(`/db/student-answers?student_id=${studentId}&material_id=${materialIdParam}`);
		const submissions = resp.data?.submissions || [];
		if (!submissions.length) return;

		// Use the first submission (student can only submit once)
		const saved = submissions[0];
		if (!saved.answers || !Array.isArray(saved.answers)) {
			// still set submitted/score if backend has them
			if (saved.status && String(saved.status).toLowerCase() === 'submitted') {
			setSubmitted(true);
			setScore(saved.total_score ?? 0);
			setSavedSubmissionTime(saved.submission_time ?? null);
			}
			return;
		}

		// Build a map of questionKey -> question object for type info
		const questionMap = {};
		questionsList.forEach((qObj, idx) => {
			const questionContent = qObj.question_content?.questions || [];
			questionContent.forEach((question, qIndex) => {
			const key = `${idx}-${qIndex}`; // same key used in UI
			questionMap[key] = question;
			});
		});

		const loadedUserAnswers = {};

		// Helper to get qObj id string robustly
		const getQObjId = (qObj) => {
			if (!qObj) return null;
			if (qObj.id) return String(qObj.id);
			if (qObj._id) {
			if (typeof qObj._id === 'string') return qObj._id;
			if (qObj._id.$oid) return qObj._id.$oid;
			return String(qObj._id);
			}
			return null;
		};

		// Map saved answers back to UI keys
		saved.answers.forEach(a => {
			const savedQid = String(a.question_id || '');
			// savedQid format expected: "<questionDocId>-<questionKey>" e.g. "6970...-0-1"
			for (let i = 0; i < questionsList.length; i++) {
			const qObj = questionsList[i];
			const qId = getQObjId(qObj);
			if (!qId) continue;
			const prefix = `${qId}-`;
			if (savedQid.startsWith(prefix)) {
				const questionKey = savedQid.slice(prefix.length); // e.g. "0-1"
				// store raw value for now; we'll normalize below using questionMap
				loadedUserAnswers[questionKey] = a.user_answer;
				break;
			}
			}
		});

		// Normalize types for multiple choice answers and text answers
		Object.keys(loadedUserAnswers).forEach(k => {
			const q = questionMap[k];
			if (!q) return;
			const val = loadedUserAnswers[k];

			if (q.questionType === 'multiple_choice') {
			// convert numeric strings to numbers; leave non-numeric as-is
			if (typeof val === 'number') {
				loadedUserAnswers[k] = val;
			} else if (typeof val === 'string' && /^\d+$/.test(val)) {
				loadedUserAnswers[k] = Number(val);
			} else {
				const n = Number(val);
				loadedUserAnswers[k] = Number.isNaN(n) ? val : n;
			}
			} else {
			// text / long answer: ensure string
			loadedUserAnswers[k] = val == null ? '' : String(val);
			}
		});

		setUserAnswers(loadedUserAnswers);
		setScore(saved.total_score ?? 0);
		setSavedSubmissionTime(saved.submission_time ?? null);
		// mark submitted if backend says so
		if (saved.status && String(saved.status).toLowerCase() === 'submitted') {
			setSubmitted(true);
		}
		} catch (err) {
		console.warn('Could not load student submission', err);
		}
	};

	useEffect(() => {
		const ac = new AbortController();
		let active = true;

		if (materialData) {
		console.log('Using AI-generated material data:', materialData);
		const slidesData = Array.isArray(materialData.slides)
			? materialData.slides
			: materialData.slides?.slides || [];

		const normalizedSlides = slidesData.map(slide => ({
			...slide,
			slidetype: slide.slideType || slide.slidetype,
		}));

		setSlides(normalizedSlides);
		setCurrentSlideIndex(0);

		const materialIdLocal = materialData.sid;
		setMaterialId(materialIdLocal); // Set material ID

		if (materialIdLocal) {
			setLoadingQuestions(true);
			axios.get(`/db/question?material_id=${materialIdLocal}`, {
			signal: ac.signal
			})
			.then(response => {
				if (!active) return;
				console.log('Questions response:', response.data);
				const questionsList = response.data?.questions || [];
				setQuestions(questionsList);
				setLoadingQuestions(false);
			})
			.catch(e => {
				console.log('No questions found yet:', e);
				setQuestions([]);
				setLoadingQuestions(false);
			});
		} else {
			setLoadingQuestions(false);
		}

		return () => {
			active = false;
			ac.abort();
		};
		}

		if (material) {
		console.log('Fetching traditional material:', material);
		setMaterialId(material.id);

		axios.get(`/db/material?material_id=${material?.id}&subject_id=${material?.subject_id}&topic=${material?.topic}&uploaded_by=${material?.uploaded_by}`, {
			signal: ac.signal,
		})
			.then(response => {
			if (!active) return;
			const slidesData = response.data.materials[0]?.slides || [];
			console.log('Fetched slides data:', slidesData);
			const slidesArray = Array.isArray(slidesData) ? slidesData : slidesData?.slides || [];
			const normalizedSlides = slidesArray.map(slide => ({
				...slide,
				slidetype: slide.slideType || slide.slidetype,
			}));
			setSlides(normalizedSlides);
			setCurrentSlideIndex(0);
			})
			.catch(e => {
			if (active) setErr('Unable to fetch slides');
			});

		setLoadingQuestions(true);
		axios.get(`/db/question?material_id=${material?.id}`, {
			signal: ac.signal
		})
			.then(response => {
			if (!active) return;
			const questionsList = response.data?.questions || [];
			setQuestions(questionsList);
			setLoadingQuestions(false);
			})
			.catch(e => {
			console.log('No questions found');
			setQuestions([]);
			setLoadingQuestions(false);
			});

		return () => {
			active = false;
			ac.abort();
		};
		}
	}, [material, materialData]);

	// After questions load, attempt to fetch saved submission
	useEffect(() => {
		const currentStudentId = userInfo?.id || localStorage.getItem('student_id');
		if (!loadingQuestions && questions.length > 0 && materialId && currentStudentId) {
			loadStudentSubmission(currentStudentId, materialId, questions);
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps

		// load answer directly if user is not a student	
		console.log('Current user role:', userRole);
		if (userRole && userRole !== 'student') {
			setSubmitted(true);
		}
	}, [loadingQuestions, questions, materialId, userInfo?.id, userRole]);
	
	// If showing edit
    if (showEdit && selectedMaterial) {
        return (
            <EditMaterial 
                material={selectedMaterial} 
                onClose={() => {
					setShowEdit(false);
					setSelectedMaterial(null);
				}}
            />
        );
    }   
	
	if (err) return (
		<div style={{ padding: '20px', color: 'red' }}>
		<p>{err}</p>
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

	return (
		<div style={{ width: '100%', maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
			<div className="back-navigation" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <button 
                onClick={handleBackToMaterials}
                className="back-button"
                aria-label="Back to subjects list"
                >
                ← Back to Materials
                </button>
				{userRole !== 'student' && (
                    <button 
                    onClick={() => handleEditMaterial(material)}
                    className="button primary"
                    aria-label="Edit current material"
                    >
                    ✏️ Edit Material
                    </button>
                )}
            </div>
		{/* ========== SLIDES SECTION ========== */}
		<div style={{
			backgroundColor: 'white',
			borderRadius: '10px',
			boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
			marginBottom: '30px',
			overflow: 'hidden',
			width: '1200px',
			height: '750px'
		}}>
			{/* Navigation Controls */}
			<div style={{
			display: 'flex',
			justifyContent: 'space-between',
			alignItems: 'center',
			padding: '15px 20px',
			backgroundColor: '#f5f5f5',
			borderBottom: '2px solid #ddd'
			}}>
			<button
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

			{/* Slide Content */}
			<div style={{
			position: 'relative',
			height: '560px',
			backgroundColor: 'white'
			}}>
			{/* Left click zone */}
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

			{/* Slide content */}
			<div style={{ padding: '40px 60px'}}>
				{renderSlide()}
			</div>

			{/* Right click zone */}
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

			{/* Progress bar */}
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

			{/* Slide Thumbnails */}
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

		{/* ========== QUESTIONS SECTION (SEPARATE) ========== */}
		<div
			style={{
			backgroundColor: 'white',
			borderRadius: '10px',
			boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
			padding: '30px',
			marginTop: '30px'
			}}
		>
			<h2 style={{
			fontSize: '24px',
			fontWeight: 'bold',
			marginBottom: '20px',
			borderBottom: '3px solid #4CAF50',
			paddingBottom: '10px'
			}}>
			📝 Practice Exercises
			</h2>

			{submitted && savedSubmissionTime && (
			<div style={{ marginBottom: '12px', color: '#666' }}>
				Submitted on: {new Date(savedSubmissionTime).toLocaleString()}
			</div>
			)}

			{loadingQuestions ? (
			<div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
				<p>Loading questions...</p>
			</div>
			) : questions.length > 0 ? (
			<div>
				<p style={{
				marginBottom: '20px',
				fontWeight: 'bold',
				color: '#4CAF50',
				fontSize: '16px'
				}}>
				✓ {(questions?.[0]?.question_content?.questions?.length ?? 0)} question(s) available
				</p>

				{questions.map((q, index) => {
				const questionContent = q.question_content?.questions || [];
				return questionContent.map((question, qIndex) => {
					const questionKey = `${index}-${qIndex}`;
					const selectedOption = userAnswers[questionKey]; // Get user selection
					const isCorrect = question.correctAnswer === selectedOption;

					return (
					<div key={questionKey} style={{
						backgroundColor: '#f9f9f9',
						padding: '20px',
						marginBottom: '20px',
						borderRadius: '8px',
						border: '1px solid #e0e0e0'
					}}>
						<div style={{
						fontWeight: 'bold',
						marginBottom: '15px',
						fontSize: '16px',
						color: '#333'
						}}>
						Question {qIndex + 1}: {question.questionText}
						{submitted && userRole === 'student' && (
							<span style={{
							marginLeft: '10px',
							fontSize: '14px',
							fontWeight: 'normal',
							color: isCorrect ? '#4CAF50' : '#f44336'
							}}>
							{isCorrect ? '✅ Correct' : '❌ Incorrect'}
							</span>
						)}
						</div>

						{question.questionType === 'multiple_choice' && question.options ? (
						<div style={{ paddingLeft: '20px' }}>
							{question.options.map((option, optIndex) => {
							const optionLetter = String.fromCharCode(65 + optIndex);
							const isSelected = selectedOption === optIndex;
							const isOptionCorrect = question.correctAnswer === optIndex;

							let optionStyle = {
								marginBottom: '8px',
								padding: '12px',
								backgroundColor: 'white',
								borderRadius: '4px',
								border: '2px solid #ddd',
								cursor: submitted ? 'default' : 'pointer',
								transition: 'all 0.2s ease'
							};

							if (submitted) {
								if (isOptionCorrect) {
								optionStyle.backgroundColor = '#e8f5e9';
								optionStyle.borderColor = '#4CAF50';
								optionStyle.color = '#2e7d32';
								} else if (isSelected) {
								optionStyle.backgroundColor = '#ffebee';
								optionStyle.borderColor = '#f44336';
								optionStyle.color = '#c62828';
								}
							} else if (isSelected) {
								optionStyle.backgroundColor = '#e3f2fd';
								optionStyle.borderColor = '#1976d2';
							}

							return (
								<div
								key={optIndex}
								style={optionStyle}
								onClick={() => {
									if (!submitted) {
									setUserAnswers(prev => ({
										...prev,
										[questionKey]: optIndex
									}));
									}
								}}
								>
								<strong>{optionLetter}.</strong> {option}
								{submitted && isOptionCorrect && (
									<span style={{ marginLeft: '10px', color: '#4CAF50' }}>✓</span>
								)}
								</div>
							);
							})}
						</div>
						) : (
						<div>
							<div style={{ marginTop: '10px', paddingLeft: '20px' }}>
							<textarea
								style={{
								width: 'calc(100% - 40px)',
								padding: '15px',
								border: '2px solid #ddd',
								borderRadius: '4px',
								fontSize: '14px',
								minHeight: '100px',
								resize: 'vertical',
								cursor: submitted ? 'default' : 'text',
								backgroundColor: submitted ? '#f9f9f9' : 'white'
								}}
								value={userAnswers[questionKey] || ''}
								disabled={submitted}
								onChange={(e) => {
								if (!submitted) {
									setUserAnswers(prev => ({
									...prev,
									[questionKey]: e.target.value
									}));
								}
								}}
								placeholder="Type your answer here..."
							/>
							</div>
						</div>
						)}

						{submitted && question.correctAnswer !== undefined && question.correctAnswer !== null && question.questionType !== 'multiple_choice' && (
						<div style={{
							marginTop: '15px',
							padding: '15px',
							backgroundColor: '#e3f2fd',
							borderRadius: '5px',
							borderLeft: '5px solid #2196F3',
							fontSize: '14px'
						}}>
							<strong>✅ Correct Answer:</strong> {question.correctAnswer}
						</div>
						)}

						{submitted && question.explanation && (
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

						{(!submitted || userRole !== 'student') && question.learningObjective && (
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
				});
				})}

				{!submitted && userRole === 'student' && (
				<div style={{
					textAlign: 'center',
					marginTop: '30px',
					padding: '20px',
					borderTop: '2px solid #e0e0e0'
				}}>
					<button
					style={{
						padding: '15px 30px',
						fontSize: '18px',
						backgroundColor: '#4CAF50',
						color: 'white',
						border: 'none',
						borderRadius: '5px',
						cursor: 'pointer',
						fontWeight: 'bold',
						boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
					}}
					onClick={async () => {
						// Calculate score
						let totalCorrect = 0;
						let totalQuestions = 0;
						const answers = [];

						questions.forEach((q, index) => {
						const questionContent = q.question_content?.questions || [];
						totalQuestions += questionContent.length;
						questionContent.forEach((question, qIndex) => {
							const questionKey = `${index}-${qIndex}`;
							const userAnswer = userAnswers[questionKey];
							const isCorrect = question.questionType === 'multiple_choice'
							? Number(userAnswer) === Number(question.correctAnswer)
							: (typeof userAnswer === 'string' && typeof question.correctAnswer === 'string')
								? userAnswer?.trim().toLowerCase() === question.correctAnswer?.trim().toLowerCase()
								: userAnswer === question.correctAnswer;

							// Collect answer data for backend storage
							// Use question document id (if available) + questionKey to create stable id
							const qDocId = q.id || (q._id && (q._id.$oid || q._id)) || q._id || '';
							const question_id = qDocId ? `${qDocId}-${questionKey}` : `${questionKey}`;

							answers.push({
							question_id: question_id,
							user_answer: userAnswer,
							is_correct: !!isCorrect,
							score: isCorrect ? 1 : 0 // Simplified score calculation, 1 point for correct answer
							});

							if (isCorrect) {
							totalCorrect++;
							}
						});
						});

						const finalScore = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;
						setScore(finalScore);

						// optimistic UI
						setSubmitted(true);
						setSubmitting(true);

						try {
						const currentStudentId = userInfo?.id || localStorage.getItem('student_id');
						const response = await axios.post('/db/student-answers-submit', {
							student_id: currentStudentId,
							material_id: materialId,
							answers: answers,
							total_score: finalScore,
							submission_time: new Date().toISOString(),
							status: "submitted"
						});

						console.log('Student answers submitted successfully:', response.data);

						// reflect backend canonical values if present
						const saved = response.data?.submission;
						if (saved) {
							setSavedSubmissionTime(saved.submission_time ?? new Date().toISOString());
							setScore(saved.total_score ?? finalScore);
							if (saved.status && String(saved.status).toLowerCase() === 'submitted') {
							setSubmitted(true);
							}
						}
						} catch (error) {
						console.error('Error submitting student answers:', error);
						// Optionally revert optimistic UI or notify user; keep submitted true so they see their answers
						} finally {
						setSubmitting(false);
						}
					}}
					>
					Submit Answers
					</button>
				</div>
				)}

				{submitted && userRole === 'student' && (
				<div style={{
					textAlign: 'center',
					marginTop: '30px',
					padding: '30px',
					backgroundColor: '#e8f5e9',
					borderRadius: '10px',
					border: '2px solid #4CAF50'
				}}>
					<h3 style={{ marginBottom: '10px', color: '#2e7d32' }}>📊 Quiz Results</h3>
					<p style={{ fontSize: '24px', fontWeight: 'bold', color: '#4CAF50' }}>
					{score}%
					</p>
					<p style={{ marginBottom: '20px', color: '#333' }}>
					You got {score}% of the questions correct!
					</p>
				</div>
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
				<p style={{ fontSize: '14px', marginTop: '10px' }}>
				Questions are being generated...
				</p>
			</div>
			)}
		</div>
		</div>
	);
}

export default ViewMaterial;
