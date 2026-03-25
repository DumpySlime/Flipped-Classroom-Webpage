import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import ViewMaterial from './ViewMaterial';
import ViewQuestion from './ViewQuestion';
import { useTranslation } from 'react-i18next';

function GenerateMaterial({subject, onClose, userInfo, userRole}) {
    const { t } = useTranslation();
	const [topics, setTopics] = useState([])
    const [loadingTopics, setLoadingTopics] = useState(false); // <-- defined
    const [topicsError, setTopicsError] = useState(null); // <-- defined
	const { t, i18n } = useTranslation();
	
    const [values, setValues] = useState({
		form: '',
		topic: '',
		sub_topics: [],
		description: '',
		subject: subject?.subject || '',
		subject_id: subject?.id || '',
		language: ''
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
				form: '',
				topic: '',
				sub_topics: [],
				language: '',
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

    // Update subject fields and fetch topics with form
    useEffect(() => {
        const subjectId = subject?._id || subject?.id || '';
        setValues(prev => ({
        ...prev,
        subject: subject?.subject || '',
        subject_id: subjectId
        }));

        if (!subjectId || !values.form) {
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
          params: { subject_id: subjectId,  form: values.form},
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
    }, [subject, values.form]);

	
	// Clear sub_topics when topic/ form changes
	useEffect(() => {
		setValues(prev => ({
			...prev,
			sub_topics: []
		}));
	}, [values.topic, values.form]);

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
		if (!values.form) {
			setError(t('selectFormWarning'));
			return;
		}		
		if (!values.topic) {
			setError(t('selectTopicWarning'));
			return;
		}
		if (!values.language) {
			setError(t('selectLanguageWarning'));
			return;
		}

		setIsGenerating(true);
		console.log('Form submitted with values:', values);
		
		// Store current values before they get reset
		const submittedValues = { ...values };
		const formData = new FormData();
		formData.append('subject', submittedValues.subject);
		formData.append('subject_id', submittedValues.subject_id);
		formData.append('form', submittedValues.form);
		formData.append('topic', submittedValues.topic);
		formData.append('sub_topics', JSON.stringify(submittedValues.sub_topics))
		formData.append('language', submittedValues.language);
		formData.append('description', submittedValues.description);

		axios.post('/api/llm/material/create', formData, {
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
			setError(t('matGenerateFailed'));
			setIsGenerating(false);
		})
	}

	// function for question generation
	const generateQuestions = (materialSid, submittedValues) => {
		const formData = new FormData();
		formData.append('subject', submittedValues.subject);
		formData.append('subject_id', submittedValues.subject_id);
		formData.append('form', submittedValues.form)
		formData.append('topic', submittedValues.topic);
		formData.append('sub_topics', JSON.stringify(submittedValues.sub_topics));
		formData.append('material_id', materialSid);
		formData.append('language', submittedValues.language);

		console.log('Generating questions with data:', Object.fromEntries(formData));
		
		axios.post('/api/ai/generate-question', formData)
		.then( (response) => {
			const data = response.data;
			console.log(`Question generation request sent successfully:`, data);
			setGeneratedQuestionId(data._id);
			setHasCreatedQuestions(true);
			
			// NOW reset the form values after everything is done
			setValues({
				form: '',
				topic: '',
				sub_topics: [],
				language: '',
				description: '',
				subject: subject?.subject || '',
				subject_id: subject?.id || '',
			});
		})
		.catch( (error) => {
			console.log(`Error sending question generation request: ${error}`);
			console.log('Error details:', error.response?.data);
			setError(t('questionGenerateFailed'));
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
		console.log('Showing generated material in view:', generatedMaterial)
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
<<<<<<< HEAD
                {t('backToMaterials')}
=======
                ← {t('backToMaterials')}
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
                </button>
			</div>

			{!generatedMaterial ? (
				<form onSubmit={handleSubmit} className="form-container">
					<h2>{t('generateMaterial')}</h2>
					
					{error && <div className="error-message">{error}</div>}

					<div className="form-group">
<<<<<<< HEAD
						<label htmlFor="subject">{t('subject')}</label>
=======
						<label htmlFor="subject">{t('subjectList')}</label>
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
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
<<<<<<< HEAD
						<label htmlFor="form">{t('form')}:</label>
=======
						<label htmlFor="form">{t('formList')}</label>
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
						<select
						id="form"
						name="form"
						value={values.form}
						onChange={handleChanges}
						className="form-input"
						>
<<<<<<< HEAD
						<option value="">{t('selectForm')}</option>
						{[1,2,3,4,5,6].map(f => (
							<option key={f} value={`form${f}`}>{t('form')} {f}</option>
=======
						<option value="">{t('selectA_')} {t('form')}</option>
						{[t('1'), t('2'), t('3'), t('4'), t('5'), t('6')].map(f => (
							<option key={f} value={`form${f}`}>{t('Form')}{f}</option>
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
						))}
						</select>
					</div>

					{values.form && (
						<div className="form-group">
<<<<<<< HEAD
						<label htmlFor="topic">{t('topic')}</label>
=======
						<label htmlFor="topic">{t('topicList')}</label>
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
						<select
							id="topic"
							name="topic"
							value={values.topic}
							onChange={handleChanges}
							className="form-input"
						>
<<<<<<< HEAD
							<option value="">{t('selectTopic')}</option>
							{topics.map(tpc => (
							<option key={tpc._id} value={tpc.topic.en}>
								{i18n.language === 'zh-HK' ? tpc.topic.zh : tpc.topic.en}
=======
							<option value="">{t('selectA_')} {t('topic')}</option>
							{topics.map(t => (
							<option key={t._id} value={t.topic}>
								{t.topic}
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
							</option>
							))}
						</select>
						</div>
					)}

					{values.topic && topics.length > 0 && (
					<div className="form-group">
<<<<<<< HEAD
						<label>{t('sub_topics')}:</label>
					<div className="checkbox-group">
					{topics.find(tpc => tpc.topic.en === values.topic)?.sub_topics?.map((sub, idx) => (
					<div key={idx} className="checkbox-item">
						<input
						type="checkbox"
						id={`sub_${idx}`}
						value={sub.en}
						checked={values.sub_topics.includes(sub.en)}
						onChange={(e) => {
							if (e.target.checked) {
							setValues(prev => ({
								...prev,
								sub_topics: [...prev.sub_topics, sub.en]
							}));
							} else {
							setValues(prev => ({
								...prev,
								sub_topics: prev.sub_topics.filter(s => s !== sub.en)
							}));
							}
						}}
						/>
						<label htmlFor={`sub_${idx}`}>
						{i18n.language === 'zh-HK' ? sub.zh : sub.en}
						</label>
					</div>
					))}
=======
						<label>{t('subTopic')}</label>
						<div className="checkbox-group">
						{topics.find(t => t.topic === values.topic)?.sub_topics?.map((sub, idx) => (
							<div key={idx} className="checkbox-item">
							<input
								type="checkbox"
								id={`sub_${idx}`}
								value={sub}
								checked={values.sub_topics.includes(sub)}
								onChange={(e) => {
								if (e.target.checked) {
									setValues(prev => ({
									...prev,
									sub_topics: [...prev.sub_topics, sub]
									}));
								} else {
									setValues(prev => ({
									...prev,
									sub_topics: prev.sub_topics.filter(s => s !== sub)
									}));
								}
								}}
							/>
							<label htmlFor={`sub_${idx}`}>{sub}</label>
							</div>
						))}
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
						</div>
					</div>
					)}

					<div className="form-group">
<<<<<<< HEAD
					<label htmlFor="language">{t('language')}:</label>
=======
					<label htmlFor="language">{t('languageList')}</label>
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
					<select
						id="language"
						name="language"
						value={values.language}
						onChange={handleChanges}
						className="form-input"
					>
<<<<<<< HEAD
						<option value="">{t('selectLanguage')}</option>
=======
						<option value="">{t('selectA_')} {t('language')}</option>
>>>>>>> bdb1089607b6ea7e6a3c8978f92960e3d290556a
						<option value="English">{t('english')}</option>
						<option value="Chinese">{t('chinese')}</option>
						{/* Add more as needed */}
					</select>
					</div>

					<div className="form-group">
						<label htmlFor="description">{t('description')}:</label>
						<textarea 
							id="description"
							name="description" 
							value={values.description} 
							onChange={handleChanges}
							placeholder={t('descriptionPlaceholder')}
							className="form-textarea"
							rows="4"
						/>
					</div>

					<button 
						type="submit" 
						disabled={isGenerating}
						className="submit-button"
					>
						{isGenerating ? t('generating') : t('generateMaterial')}
					</button>
				</form>
			) : isGenerating ? (
				<div className="loading-container">
					<p>{t('generateLoadingMessage')}</p>
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
