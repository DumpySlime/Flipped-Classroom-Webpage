import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import SlideExplanation from './slide-template/SlideExplanation';
import SlideExample from './slide-template/SlideExample';

function ViewMaterial({ material, materialData, props}) {
	const [slides, setSlides] = useState(null);
	const [questions, setQuestions] = useState([]);
	const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
	const [err, setErr] = useState(null);
	const [loadingQuestions, setLoadingQuestions] = useState(true);
	const [userAnswers, setUserAnswers] = useState({});
	const [submitted, setSubmitted] = useState(false);
	const [score, setScore] = useState(0);
	const [resetKey, setResetKey] = useState(0);
	const [materialId, setMaterialId] = useState(null); 

	useEffect(() => {
		const ac = new AbortController();
		let active = true;

		if (materialData) {
			console.log("Using AI-generated material data:", materialData);
			
			const slidesData = Array.isArray(materialData.slides)
				? materialData.slides
				: materialData.slides?.slides || [];

			const normalizedSlides = slidesData.map(slide => ({
				...slide,
				slidetype: slide.slideType || slide.slidetype,
			}));
			
			setSlides(normalizedSlides);
			setCurrentSlideIndex(0);

			const materialId = materialData.sid;
			setMaterialId(materialId); // Set material ID
			if (materialId) {
				setLoadingQuestions(true);
				axios.get(`/db/question?material_id=${materialId}`, {
					signal: ac.signal
				})
				.then(response => {
					if (!active) return;
					console.log("Questions response:", response.data);
					const questionsList = response.data?.questions || [];
					setQuestions(questionsList);
					setLoadingQuestions(false);
				})
				.catch(e => {
					console.log("No questions found yet:", e);
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
			console.log("Fetching traditional material:", material);
			setMaterialId(material.id); 
			
			axios.get(`/db/material?material_id=${material?.id}&subject_id=${material?.subject_id}&topic=${material?.topic}&uploaded_by=${material?.uploaded_by}`, {
				signal: ac.signal,
			})
			.then(response => {
				if (!active) return;
				const slidesData = response.data.materials[0]?.slides || [];
				console.log("Fetched slides data:", slidesData);
				const slidesArray = Array.isArray(slidesData)
					? slidesData
					: slidesData?.slides || [];

				const normalizedSlides = slidesArray.map(slide => ({
					...slide,
					slidetype: slide.slideType || slide.slidetype,
				}));
				setSlides(normalizedSlides);
				setCurrentSlideIndex(0);
			})
			.catch(e => {
				if (active) setErr("Unable to fetch slides");
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
				console.log("No questions found");
				setQuestions([]);
				setLoadingQuestions(false);
			});

			return () => {
				active = false;
				ac.abort();
			};
		}

	}, [material, materialData]);

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
			{/* ========== SLIDES SECTION ========== */}
			<div style={{
				backgroundColor: 'white',
				borderRadius: '10px',
				boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
				marginBottom: '30px',
				overflow: 'hidden'
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
					minHeight: '400px',
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
					<div style={{ padding: '40px 60px' }}>
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
				key={resetKey} 
				style={{
				backgroundColor: 'white',
				borderRadius: '10px',
				boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
				padding: '30px',
				marginTop: '30px'
			}}>
				<h2 style={{ 
					fontSize: '24px', 
					fontWeight: 'bold', 
					marginBottom: '20px',
					borderBottom: '3px solid #4CAF50',
					paddingBottom: '10px'
				}}>
					📝 Practice Exercises
				</h2>

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
							✓ {questions.length} question(s) available
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
											{submitted && (
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
										
										{!submitted && question.learningObjective && (
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
						
						{!submitted && (
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
													? userAnswer === question.correctAnswer 
													: userAnswer?.trim().toLowerCase() === question.correctAnswer?.trim().toLowerCase();
												
												// Collect answer data for backend storage
												answers.push({
													question_id: `${q.id}-${questionKey}`, // Use unique question identifier
													user_answer: userAnswer,
													is_correct: isCorrect,
													score: isCorrect ? 1 : 0 // Simplified score calculation, 1 point for correct answer
												});
												
												// Only check correctness for multiple choice questions
												if (isCorrect) {
													totalCorrect++;
												}
											});
										});
										
										const finalScore = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;
										setScore(finalScore);
										setSubmitted(true);
										
										// Send answers to backend for storage
										try {
											
											const currentStudentId = props?.userInfo?.id || localStorage.getItem('student_id');
											
											const response = await axios.post('/db/student-answers-submit', {
												student_id: currentStudentId,
												material_id: materialId, 
												answers: answers,
												total_score: finalScore,
												submission_time: new Date().toISOString()
											});
											console.log('Student answers submitted successfully:', response.data);
										} catch (error) {
											console.error('Error submitting student answers:', error);
										}
									}}
								>
									Submit Answers
								</button>
							</div>
						)}
						
						{submitted && (
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
								<button 
									style={{
										padding: '10px 20px',
										fontSize: '16px',
										backgroundColor: '#2196F3',
										color: 'white',
										border: 'none',
										borderRadius: '5px',
										cursor: 'pointer'
									}}
									onClick={() => {
										setSubmitted(false);
										setUserAnswers({});
										setScore(0);
										// Update resetKey
										setResetKey(prev => prev + 1);
									}}
								>
									Try Again
								</button>
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
