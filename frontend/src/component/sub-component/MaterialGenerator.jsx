import { useState, useEffect } from 'react';
import '../../styles.css';
import '../../dashboard.css';

function MaterialGenerator({ activeSection }) {
	const [allSubject, setAllSubject] = useState([]);
	const [allRelatedTopic, setAllRelatedTopic] = useState([]);
	const [values, setValues] = useState({
		subject: '',
		topic:'' ,
		instruction:'' ,
	});

	//const [loadingSubject, setLoadingSubject] = useState(false);
	const [error, setError] = useState(null)

	const handleChanges = (e) => {
		setValues({...values, [e.target.name]:[e.target.value]})
	}

	const handleGenerateMaterial = () => {
		axios.post('/api/llm/query', values)
		.catch(function (e) {
			console.error('Error generating material:', e);
			if (e.name !== 'AbortError') setError('Failed to generate material');
		});
	}

	useEffect(() => {
		if (activeSection === 'material-generator') return;
		const ac = AbortController();

		console.log('Fetching Subject...')
		(() => {
			//setLoadingSubject(true);
			setError(null);
			axios.get('/db/subject')
			.then(function (response) {
				const data = response.data;
				console.log('Fetched subject data:', data);
				const list = (data.subjects || []).map(s => ({
					subject: s.subject,
					topics: s.topics
				}))
				setAllSubject(list);
				const tlist = (list.topics || []).map(t => ({
					topic: t.topic
				}))
				setAllRelatedTopic(tlist);
			})
			.catch(function (error) {
				if (error.name !== 'AbortError') setError('Failed to load teachers');
			})
			.finally(function () {
				//setLoadingSubject(false);
			})
		})();
		return () => ac.abort();
	}, [activeSection]);

	return (
		<form className="material-generator-section">
		<h3>Material Generator</h3>
		
		<div className="ai-generator">
			<div className="form-group">
				<label htmlFor="material-subject-select">Subject</label>
				<select id="subject-select" className="select" onChange={(e) => handleChanges(e)} required value={values.subject}>
					<option value="">-- Choose subject --</option>
					{
					allSubject.map(s => {
						return (
							<option value={s.subject}>{s.subject}</option>
						)
					})
					}
				</select>
			</div>
			
			<div className="form-group">
				<label htmlFor="material-topic-select">Content Topic</label>
				<select id="topic-select" className="select" onChange={(e) => handleChanges(e)} required value={values.topic}>
					{
					allRelatedTopic.map(t => {
						return (
							<option value={t.topic}>{t.topic}</option>
						)
					})
					}
				</select>
			</div>
			
			<div className="form-group">
				<label htmlFor="material-instructions-input">Additional Instructions</label>
				<textarea
					id="material-instructions-input"
					placeholder="Provide more details for the AI content generation..."
					rows="4"
					className="textarea-input"
					value={values.instruction}
				></textarea>
			</div>
			
			<button 
				onClick={() => handleGenerateMaterial('content')}
				className="button"
			>
			Generate Content
			</button>
			
			
		</div>
		
		<div className="content-templates">
			<h4>Content Templates</h4>
			<p className="templates-description">Quick-start templates for common teaching materials</p>
			<div className="templates-list">
			<div className="template-card">
				<h5>Lecture Notes</h5>
				<p>Comprehensive notes with key points and explanations</p>
				<button className="use-template-button">Use Template</button>
			</div>
			<div className="template-card">
				<h5>Multiple Choice Quiz</h5>
				<p>Assessment with multiple choice questions</p>
				<button className="use-template-button">Use Template</button>
			</div>
			<div className="template-card">
				<h5>Practice Worksheet</h5>
				<p>Exercises for students to apply concepts</p>
				<button className="use-template-button">Use Template</button>
			</div>
			<div className="template-card">
				<h5>Presentation Outline</h5>
				<p>Structure for effective classroom presentations</p>
				<button className="use-template-button">Use Template</button>
			</div>
			</div>
		</div>
		</form>
	);
}

export default MaterialGenerator;