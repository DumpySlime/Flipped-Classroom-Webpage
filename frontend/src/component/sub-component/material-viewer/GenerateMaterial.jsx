import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import { apiRequest } from '../../../services/api';
import ViewMaterial from './ViewMaterial';
import ViewQuestion from './ViewQuestion';
import { useTranslation } from 'react-i18next';
import { getLangText } from '../../../utils/langText';

function GenerateMaterial({subject, onClose, userInfo, userRole}) {
    const { t, i18n } = useTranslation();
    const lang = i18n.language === 'zh-HK' ? 'zh' : 'en';

    const getText = (key) => {
        const val = t(key);
        if (val && typeof val === 'object') {
            return val['en'] || val['zh'] || Object.values(val)[0] || key;
        }
        return val;
    };

    const [topics, setTopics] = useState([]);
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
    });

    const [error, setError] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedMaterial, setGeneratedMaterial] = useState(null);
    const [hasCreatedQuestions, setHasCreatedQuestions] = useState(false);
    const [generatedQuestionId, setGeneratedQuestionId] = useState(null);
    const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
    const [generatedVideos, setGeneratedVideos] = useState([]);
    const [showView, setShowView] = useState(false);

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
                const res = await apiRequest(`/db/topic?subject_id=${subjectId}&form=${values.form}`);

                const fetched = Array.isArray(res?.topics) ? res.topics : [];
                if (!cancelled) {
                    setTopics(fetched);
                    setValues(prev => {

                        const stillValid = fetched.some(
                            topic => getLangText(topic.topic, lang) === prev.topic
                        );
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
    }, [subject, values.form])
	// Clear sub_topics when topic/ form changes
	useEffect(() => {
		setValues(prev => ({
			...prev,
			sub_topics: []
		}));
	}, [values.topic, values.form]);

    const subjectId = subject?._id || subject?.id;
    if (!subjectId) return null;

    const handleChanges = (e) => {
        setValues({ ...values, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!values.form)     { setError(getText('selectFormWarning'));     return; }
        if (!values.topic)    { setError(getText('selectTopicWarning'));    return; }
        if (!values.language) { setError(getText('selectLanguageWarning')); return; }

        setIsGenerating(true);
        const submittedValues = { ...values };
        const formData = new FormData();
        formData.append('subject',     submittedValues.subject);
        formData.append('subject_id',  submittedValues.subject_id);
        formData.append('form',        submittedValues.form);
        formData.append('topic',       submittedValues.topic);
        formData.append('sub_topics',  JSON.stringify(submittedValues.sub_topics));
        formData.append('language',    submittedValues.language);
        formData.append('description', submittedValues.description);

        try {
            const response = await apiRequest('/api/llm/material/create', {
                method: 'POST',
                body: formData
            });

            const data = response || {};
            console.log('[DEBUG] Full LLM response:', JSON.stringify(data));
            console.log('[DEBUG] LLM create response keys:', Object.keys(data));
            console.log('[DEBUG] data.sid:', data.data.sid);
            console.log('[DEBUG] data.material_id:', data.data.material_id);
            console.log('[DEBUG] data._id:', data.data._id);
            setError(null);
            setGeneratedMaterial(data);
            const materialSid = data.data.sid || data.data.material_id || data.data._id;
            console.log('[DEBUG] materialSid resolved to:', materialSid);
            generateQuestions(materialSid, submittedValues);
        } catch (error) {
            console.log(`Error sending material generation parameters: ${error}`);
            setError(getText('matGenerateFailed'));
            setIsGenerating(false);
        }
    };

    const generateVideo = async (materialId) => {
        console.log('[DEBUG] generateVideo called with materialId:', materialId);
        console.log('[DEBUG] generatedMaterial:', generatedMaterial);
        if (!materialId) {
            console.error('[ERROR] materialId is undefined, skipping video generation');
            setShowView(true);  // 跳過 video，直接顯示 material
            return;
        }
        setIsGeneratingVideo(true);
        console.log(`Generating videos for material: ${materialId}`);

        try {
            const response = await apiRequest('/api/generate-video/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ material_id: materialId, quality: "medium" })
            });

            const videos = response?.videos || [];
            console.log("Videos generated:", videos);
            setGeneratedVideos(videos);
        } catch (error) {
            console.error("Video generation failed:", error);
            console.warn("Video generation failed but material and questions are ready.");
        } finally {
            setIsGeneratingVideo(false);
            setShowView(true);
        }
    };

    const generateQuestions = async (materialSid, submittedValues) => {
        const formData = new FormData();
        formData.append('subject',     submittedValues.subject);
        formData.append('subject_id',  submittedValues.subject_id);
        formData.append('form',        submittedValues.form);
        formData.append('topic',       submittedValues.topic);
        formData.append('sub_topics',  JSON.stringify(submittedValues.sub_topics));
        formData.append('material_id', materialSid);
        formData.append('language',    submittedValues.language);

        try {
            const response = await apiRequest('/api/ai/generate-question', {
                method: 'POST',
                body: formData
            });

            const data = response;
            console.log(`Question generation successful:`, data);
            setGeneratedQuestionId(data._id);
            setHasCreatedQuestions(true);
            setValues({
                form: '',
                topic: '',
                sub_topics: [],
                language: '',
                description: '',
                subject: subject?.subject || '',
                subject_id: subject?.id || '',
            });

            setIsGenerating(false);  // 先停 question loading

            // 然後立刻開始 video（isGeneratingVideo 會在 generateVideo 裡 setIsGeneratingVideo(true)）
            await generateVideo(materialSid);

        } catch (error) {
            console.log(`Error sending question generation request: ${error}`);
            console.log('Error details:', error);
            setError(getText('questionGenerateFailed'));
            setGeneratedMaterial(null);
            setIsGenerating(false);  // catch 裡也要停
        }
        // 沒有 finally，手動在 try/catch 各自處理
    };

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
                {getText('backToMaterials')}
                </button>
            </div>

            {!generatedMaterial ? (
                <form onSubmit={handleSubmit} className="form-container">
                    <h2>{getText('generateMaterial')}</h2>

                    {error && <div className="error-message">{error}</div>}

                    <div className="form-group">
                        <label htmlFor="subject">{getText('subjectList')}</label>
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
                        <label htmlFor="form">{getText('formList')}</label>
                        <select id="form" name="form" value={values.form} onChange={handleChanges} className="form-input">
                            <option value="">{getText('selectA_')} {getText('form')}</option>
                            {[
                                { value: 'form1', label: getText('formOne') },
                                { value: 'form2', label: getText('formTwo') },
                                { value: 'form3', label: getText('formThree') },
                                { value: 'form4', label: getText('formFour') },
                                { value: 'form5', label: getText('formFive') },
                                { value: 'form6', label: getText('formSix') },
                            ].map(({ value, label }) => (
                                <option key={value} value={value}>{label}</option>
                            ))}
                        </select>
                    </div>

                    {values.form && (
                        <div className="form-group">
                            <label htmlFor="topic">{getText('topicList')}</label>
                            <select id="topic" name="topic" value={values.topic} onChange={handleChanges} className="form-input">
                                <option value="">{getText('selectA_')} {getText('topic')}</option>
                                {topics.map(topic => (
                                    <option
                                        key={topic._id}
                                        value={getLangText(topic.topic, lang)}
                                    >
                                        {getLangText(topic.topic, lang)}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {values.topic && topics.length > 0 && (
                        <div className="form-group">
                            <label>{getText('subTopic')}</label>
                            <div className="checkbox-group">
                                {topics.find(topic =>
                                    getLangText(topic.topic, lang) === values.topic
                                )?.sub_topics?.map((sub, idx) => {
                                    const subText = getLangText(sub, lang);
                                    return (
                                        <div key={idx} className="checkbox-item">
                                            <input
                                                type="checkbox"
                                                id={`sub_${idx}`}
                                                value={subText}
                                                checked={values.sub_topics.includes(subText)}
                                                onChange={(e) => {
                                                    if (e.target.checked) {
                                                        setValues(prev => ({
                                                            ...prev,
                                                            sub_topics: [...prev.sub_topics, subText]
                                                        }));
                                                    } else {
                                                        setValues(prev => ({
                                                            ...prev,
                                                            sub_topics: prev.sub_topics.filter(s => s !== subText)
                                                        }));
                                                    }
                                                }}
                                            />
                                            <label htmlFor={`sub_${idx}`}>{subText}</label>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="language">{getText('languageList')}</label>
                        <select id="language" name="language" value={values.language} onChange={handleChanges} className="form-input">
                            <option value="">{getText('selectA_')} {getText('language')}</option>
                            <option value="English">{getText('english')}</option>
                            <option value="Traditional Chinese">{getText('chinese')}</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label htmlFor="description">{getText('description')}:</label>
                        <textarea
                            id="description"
                            name="description"
                            value={values.description}
                            onChange={handleChanges}
                            placeholder={getText('descriptionPlaceholder')}
                            className="form-textarea"
                            rows="4"
                        />
                    </div>

                    <button type="submit" disabled={isGenerating} className="submit-button">
                        {isGenerating ? getText('generating') : getText('generateMaterial')}
                    </button>
                </form>
            ) : (isGenerating || isGeneratingVideo) ? (
                <div className="loading-container">
                    {isGenerating && <p>{getText('generateLoadingMessage')}</p>}
                    {isGeneratingVideo && <p>🎬 {getText('generating')}</p>}
                </div>
            ) : !showView ? (
                <div className="loading-container">
                    <p>⏳ Preparing...</p>
                </div>
            ) : (
                <div className="result-container">
                    {generatedVideos.length > 0 && (
                        <div className="alert alert-success" style={{ marginBottom: '1rem' }}>
                            ✅ {generatedVideos.length} video(s) generated successfully!
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default GenerateMaterial;