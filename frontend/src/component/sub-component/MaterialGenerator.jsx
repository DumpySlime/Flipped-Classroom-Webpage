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

const [loadingSubject, setLoadingSubject] = useState(false);
const [error, setError] = useState(null)

const handleChanges = (e) => {
	setValues({...values, [e.target.name]:[e.target.value]})
}

useEffect(() => {
	if (activeSection === 'material-generator') return;
	const ac = AbortController();

	console.log('Fetching Subject...')
	(async () => {
		try {
			setLoadingSubject(true);
			setError(null);
			const res = await fetch('/db/subject')
		} catch (e) {
			if (e.name !== 'AbortError') setError('Failed to load teachers')
		} finally {
			setLoadingSubject(false);
		}
	})();
	return () => ac.abort();
}, [activeSection]);

return (
	<form className="content-generator-section">
	<h3>Content Generator</h3>
	
	<div className="ai-generator">
		<div className="form-group">
		<label htmlFor="material-subject-select">Subject</label>
		<select id="subject-select" className="select" onChange={(e) => handleChanges(e)} required value={values.subject}>
			<option value="">-- Choose subject --</option>
			{
			allSubject.map(s => {
				
			})
			}
		</select>
		</div>
		
		<div className="form-group">
		<label htmlFor="material-topic-select">Content Topic</label>
		<select id="topic-select" className="select" onChange={(e) => handleChanges(e)} required value={values.topic}>
			{
			allRelatedTopic.map(t => {

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
		></textarea>
		</div>
		
		<button 
			onClick={() => handleGenerateMaterial('content')}
			className="generate-button"
			disabled={loading}
		>
		{loading ? 'Generating Content...' : 'Generate Content'}
		</button>
		
		{message2 && (
		<div className={`message ${message2.includes('success') ? 'success' : 'error'}`}>
			{message2}
		</div>
		)}
	</div>
	
	<div className="generated-content">
		<h4>Your AI-generated Educational Content</h4>
		<div className="content-list">
		{mockGeneratedContent.map(content => (
			<div key={content.id} className="content-card">
			<div className="content-info">
				<h5>{content.title}</h5>
				<p>{content.type}</p>
				<p className="content-date">Generated on {content.generationDate}</p>
				{content.wordCount && <p>Word Count: {content.wordCount}</p>}
				{content.questionCount && <p>Questions: {content.questionCount}</p>}
				{content.problemCount && <p>Problems: {content.problemCount}</p>}
			</div>
			<div className="content-actions">
				<button className="view-button">View</button>
				<button className="download-button">Download</button>
			</div>
			</div>
		))}
		</div>
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