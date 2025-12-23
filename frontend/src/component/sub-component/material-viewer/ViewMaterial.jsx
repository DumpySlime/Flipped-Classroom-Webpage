import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import SlideExplanation from './slide-template/SlideExplanation';
import SlideExample from './slide-template/SlideExample';

function ViewMaterial({ material, materialData }) {
	const [slides, setSlides] = useState(null);
	const [questions, setQuestions] = useState([]);
	const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
	const [err, setErr] = useState(null);
	const [loadingQuestions, setLoadingQuestions] = useState(true);

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
			<div style={{
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
							return questionContent.map((question, qIndex) => (
								<div key={`${index}-${qIndex}`} style={{
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
									</div>
									
									{question.questionType === 'multiple_choice' && question.options ? (
										<div style={{ paddingLeft: '20px' }}>
											{question.options.map((option, optIndex) => (
												<div key={optIndex} style={{ 
													marginBottom: '8px',
													padding: '8px',
													backgroundColor: 'white',
													borderRadius: '4px'
												}}>
													<strong>{String.fromCharCode(65 + optIndex)}.</strong> {option}
												</div>
											))}
										</div>
									) : null}
									
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
							));
						})}
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
