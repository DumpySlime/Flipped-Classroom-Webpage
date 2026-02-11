import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import ViewMaterial from './ViewMaterial';
import ViewQuestion from './ViewQuestion';

function GenerateMaterial({subject, onClose, userInfo, userRole}) {
	const [topics, setTopics] = useState([])
    const [loadingTopics, setLoadingTopics] = useState(false); // <-- defined
    const [topicsError, setTopicsError] = useState(null); // <-- defined
	
    const [values, setValues] = useState({
		topic: '',
		description: '',
		subject: subject?.subject || '',
		subject_id: subject?.id || '',
	})

	const [error, setError] = useState(null);
	const [isGenerating, setIsGenerating] = useState(false);
	const [generatedMaterial, setGeneratedMaterial] = useState(null);
	const [hasCreatedQuestions, setHasCreatedQuestions] = useState(false);
	const [generatedQuestionId, setGeneratedQuestionId] = useState(null);
    
    const [showView, setShowView] = useState(false);

	function handleViewMaterial() {
        setShowView(true);
    }

	function handleBackToMaterials() {
		setTopics([]);
		setLoadingTopics(false);
		setTopicsError(null);
		setValues({
			topic: '',
			description: '',
			subject: subject?.subject || '',
			subject_id: subject?.id || '',
		});
		setIsGenerating(false);
		setHasCreatedQuestions(false);
		setGeneratedQuestionId(null);
		setGeneratedMaterial(null);

		onClose();
	}

    // Update subject fields and fetch topics
    useEffect(() => {
        const subjectId = subject?._id || subject?.id || '';
        setValues(prev => ({
        ...prev,
        subject: subject?.subject || '',
        subject_id: subjectId
        }));

        if (!subjectId) {
        setTopics([]);
        setTopicsError(null);
        return;
        }

        let cancelled = false;
        const fetchTopics = async () => {
        setLoadingTopics(true);
        setTopicsError(null);
        try {
        const res = await axios.get('/db/topic', {
          params: { subject_id: subjectId },
        });

        const fetched = Array.isArray(res.data?.topics) ? res.data.topics : [];
        if (!cancelled) {
          setTopics(fetched);
          // Clear selected topic if it's no longer valid
          setValues(prev => {
            const stillValid = fetched.some(t => t.topic === prev.topic);
            return { ...prev, topic: stillValid ? prev.topic : '' };
          });
        }            
        } catch (err) {
            if (!cancelled) {
            setTopics([]);
            setTopicsError(err.message || 'Unable to load topics');
            }
        } finally {
            if (!cancelled) setLoadingTopics(false);
        }
        };

        fetchTopics();
        return () => { cancelled = true; };
    }, [subject]);

    // if no subject id, clear topics
    const subjectId = subject?._id || subject?.id;
    if (!subjectId) {
      setTopics([]);
      return;
    }

	const handleChanges = (e) => {
		setValues({...values, [e.target.name]: e.target.value })
	}

	const handleSubmit = (e) => {
		e.preventDefault();
		if (!values.topic) {
			setError("Please select a topic.");
			return;
		}
		setIsGenerating(true);
		console.log('Form submitted with values:', values);
		
		// Store current values before they get reset
		const submittedValues = { ...values };
		
		axios.post('/api/llm/material/create', values, {
			headers: { 'Content-Type': 'multipart/form-data' }
		})
		.then(function (response) {
			const data = response.data?.data || {};
			//console.log(`Material generation request sent successfully:`, data);
			const sid = data.sid;
			if (sid) {
				console.log(`Material task created with sid: ${sid}`);
				/** For now no polling required since we're doing synchronous generation */

				// Pass the submitted values to polling
				//pollMaterialProgress(sid, submittedValues);
			}
			// OLD synchronous handling below - to be removed
			console.log("Generated material data:", data);
			setError(null);
			setGeneratedMaterial(data);
			// Pass the submitted values to question generation
			generateQuestions(data.sid, submittedValues);
		
			// DON'T reset values here - wait until after questions are generated
		})
		.catch(function (error) {
			console.log(`Error sending material generation parameters: ${error}`);
			setError("Failed to generate material. Please try again.");
			setIsGenerating(false);
		})
	}

	// function for question generation
	const generateQuestions = (materialSid, submittedValues) => {
		const formData = new FormData();
		formData.append('subject', submittedValues.subject);
		formData.append('subject_id', submittedValues.subject_id);
		formData.append('topic', submittedValues.topic);
		formData.append('material_id', materialSid);
		
		console.log('Generating questions with data:', Object.fromEntries(formData));
		
		axios.post('/api/ai/generate-question', formData)
		.then( (response) => {
			const data = response.data;
			console.log(`Question generation request sent successfully:`, data);
			setGeneratedQuestionId(data._id);
			setHasCreatedQuestions(true);
			
			// NOW reset the form values after everything is done
			setValues({
				topic: '',
				description: '',
				subject: subject?.subject || '',
				subject_id: subject?.id || '',
				//username: username || '',
			});
		})
		.catch( (error) => {
			console.log(`Error sending question generation request: ${error}`);
			console.log('Error details:', error.response?.data);
			setError("Failed to send question generation request.");
		})
		.finally(() => setIsGenerating(false) )
	}

	if (!subject) {
		return (
			<div className="container">
				<p>Loading subject information...</p>
			</div>
		);
	}

    // If showing view
    if (showView) {
        return (
            <ViewMaterial 
                materialData={generatedMaterial} 
                userInfo={userInfo}
                userRole={userRole}
                onClose={() => {
					setShowView(false);
					handleBackToMaterials();
				}}
            />
        );
    }

	return (
		<div className="container">
			<div className="back-navigation">
                <button 
                onClick={handleBackToMaterials}
                className="back-button"
                aria-label="Back to subjects list"
                >
                ← Back to Materials
                </button>
			</div>
			{!generatedMaterial ? (
				<form onSubmit={handleSubmit} className="form-container">
					<h2>Generate Material</h2>
					
					{error && <div className="error-message">{error}</div>}

					<div className="form-group">
						<label htmlFor="subject">Subject:</label>
						<input 
							type="text" 
							id="subject"
							name="subject" 
							value={values.subject} 
							disabled 
							className="form-input"
						/>
					</div>

					<div className="form-group">
						<label htmlFor="topic">Topic:</label>
						<select 
							id="topic"
							name="topic" 
							value={values.topic} 
							onChange={handleChanges}
							className="form-input">
                            <option value="">Select a topic</option>
                                {topics.map(t => (
                                    <option key={t._id} value={t.topic}>
                                {t.topic}
                            </option>
                            ))}
						</select>
					</div>

					<div className="form-group">
						<label htmlFor="description">Description:</label>
						<textarea 
							id="description"
							name="description" 
							value={values.description} 
							onChange={handleChanges}
							placeholder="Enter additional details for material generation"
							className="form-textarea"
							rows="4"
						/>
					</div>

					<button 
						type="submit" 
						disabled={isGenerating}
						className="submit-button"
					>
						{isGenerating ? 'Generating...' : 'Generate Material'}
					</button>
				</form>
			) : isGenerating ? (
				<div className="loading-container">
					<p>Generating your material, please wait...</p>
				</div>
			) : (
				<div className="result-container">
					{handleViewMaterial()}
				</div>
			)}
		</div>
	);
}

export default GenerateMaterial;
