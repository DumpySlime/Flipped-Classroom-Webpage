import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import ViewMaterial from './ViewMaterial';
import ViewQuestion from './ViewQuestion';
import { useTranslation } from 'react-i18next';

const API_BASE_URL = "http://localhost:5000";

function GenerateMaterial({subject, onClose, userInfo, userRole}) {
    const { t } = useTranslation();
    const [topics, setTopics] = useState([])
    const [loadingTopics, setLoadingTopics] = useState(false);
    const [topicsError, setTopicsError] = useState(null);
    
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
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false); 
    const [generatedVideos, setGeneratedVideos] = useState([]);         

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
        setIsGeneratingVideo(false); 
        setGeneratedVideos([]);       
        onClose();
    }

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
                    params: { subject_id: subjectId, form: values.form },
                });

                const fetched = Array.isArray(res.data?.topics) ? res.data.topics : [];
                if (!cancelled) {
                    setTopics(fetched);
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

    useEffect(() => {
        setValues(prev => ({ ...prev, sub_topics: [] }));
    }, [values.topic, values.form]);

    const subjectId = subject?._id || subject?.id;
    if (!subjectId) {
        setTopics([]);
        return;
    }

    const handleChanges = (e) => {
        setValues({ ...values, [e.target.name]: e.target.value });
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!values.form) { setError(t('selectFormWarning')); return; }
        if (!values.topic) { setError(t('selectTopicWarning')); return; }
        if (!values.language) { setError(t('selectLanguageWarning')); return; }

        setIsGenerating(true);
        const submittedValues = { ...values };
        const formData = new FormData();
        formData.append('subject', submittedValues.subject);
        formData.append('subject_id', submittedValues.subject_id);
        formData.append('form', submittedValues.form);
        formData.append('topic', submittedValues.topic);
        formData.append('sub_topics', JSON.stringify(submittedValues.sub_topics));
        formData.append('language', submittedValues.language);
        formData.append('description', submittedValues.description);

        axios.post('/api/llm/material/create', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        .then(function (response) {
            const data = response.data?.data || {};
            console.log("Generated material data:", data);
            setError(null);
            setGeneratedMaterial(data);
            generateQuestions(data.sid, submittedValues);
        })
        .catch(function (error) {
            console.log(`Error sending material generation parameters: ${error}`);
            setError(t('matGenerateFailed'));
            setIsGenerating(false);
        });
    }

    const generateVideo = (materialId) => {
        setIsGeneratingVideo(true);
        console.log(`Generating videos for material: ${materialId}`);

        axios.post(
            `${API_BASE_URL}/api/generate-video/generate`,
            { material_id: materialId, quality: "medium" },
            { timeout: 10 * 60 * 1000 }
        )
        .then((response) => {
            const videos = response.data?.videos || [];
            console.log("Videos generated:", videos);
            setGeneratedVideos(videos);
        })
        .catch((error) => {
            console.error("Video generation failed:", error);
            console.warn("Video generation failed but material and questions are ready.");
        })
        .finally(() => {
            setIsGeneratingVideo(false);
        });
    };
    // ──────────────────────────────────────────────────────────────────────

    const generateQuestions = (materialSid, submittedValues) => {
        const formData = new FormData();
        formData.append('subject', submittedValues.subject);
        formData.append('subject_id', submittedValues.subject_id);
        formData.append('form', submittedValues.form);
        formData.append('topic', submittedValues.topic);
        formData.append('sub_topics', JSON.stringify(submittedValues.sub_topics));
        formData.append('material_id', materialSid);
        formData.append('language', submittedValues.language);

        axios.post('/api/ai/generate-question', formData)
        .then((response) => {
            const data = response.data;
            console.log(`Question generation successful:`, data);
            setGeneratedQuestionId(data._id);
            setHasCreatedQuestions(true);

            generateVideo(materialSid);

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
        .catch((error) => {
            console.log(`Error sending question generation request: ${error}`);
            console.log('Error details:', error.response?.data);
            setError(t('questionGenerateFailed'));
        })
        .finally(() => setIsGenerating(false));
    }

    if (!subject) {
        return (
            <div className="container">
                <p>Loading subject information...</p>
            </div>
        );
    }

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
                    ← {t('backToMaterials')}
                </button>
            </div>

            {!generatedMaterial ? (
                <form onSubmit={handleSubmit} className="form-container">
                    <h2>{t('generateMaterial')}</h2>

                    {error && <div className="error-message">{error}</div>}

                    <div className="form-group">
                        <label htmlFor="subject">{t('subjectList')}</label>
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
                        <label htmlFor="form">{t('formList')}</label>
                        <select id="form" name="form" value={values.form} onChange={handleChanges} className="form-input">
                            <option value="">{t('selectA_')} {t('form')}</option>
                            {[t('1'), t('2'), t('3'), t('4'), t('5'), t('6')].map(f => (
                                <option key={f} value={`form${f}`}>{t('Form')}{f}</option>
                            ))}
                        </select>
                    </div>

                    {values.form && (
                        <div className="form-group">
                            <label htmlFor="topic">{t('topicList')}</label>
                            <select id="topic" name="topic" value={values.topic} onChange={handleChanges} className="form-input">
                                <option value="">{t('selectA_')} {t('topic')}</option>
                                {topics.map(t => (
                                    <option key={t._id} value={t.topic}>{t.topic}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    {values.topic && topics.length > 0 && (
                        <div className="form-group">
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
                                                    setValues(prev => ({ ...prev, sub_topics: [...prev.sub_topics, sub] }));
                                                } else {
                                                    setValues(prev => ({ ...prev, sub_topics: prev.sub_topics.filter(s => s !== sub) }));
                                                }
                                            }}
                                        />
                                        <label htmlFor={`sub_${idx}`}>{sub}</label>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="language">{t('languageList')}</label>
                        <select id="language" name="language" value={values.language} onChange={handleChanges} className="form-input">
                            <option value="">{t('selectA_')} {t('language')}</option>
                            <option value="English">{t('english')}</option>
                            <option value="Chinese">{t('chinese')}</option>
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

                    <button type="submit" disabled={isGenerating} className="submit-button">
                        {isGenerating ? t('generating') : t('generateMaterial')}
                    </button>
                </form>
            ) : isGenerating ? (
                <div className="loading-container">
                    <p>{t('generateLoadingMessage')}</p>
                </div>
           // NEW
			) : (isGenerating || isGeneratingVideo) ? (
				<div className="loading-container">
					{isGenerating && <p>{t('generateLoadingMessage')}</p>}
					{isGeneratingVideo && <p>🎬 Generating videos, please wait...</p>}
				</div>
			) : (
				<div className="result-container">
					{generatedVideos.length > 0 && (
						<div className="alert alert-success" style={{ marginBottom: '1rem' }}>
							✅ {generatedVideos.length} video(s) generated successfully!
						</div>
					)}
					{handleViewMaterial()}
				</div>
			)}
        </div>
    );
}

export default GenerateMaterial;