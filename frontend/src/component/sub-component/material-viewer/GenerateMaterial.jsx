import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import ViewMaterial from './ViewMaterial';
import ViewQuestion from './ViewQuestion';

function GenerateMaterial({subject, username, onClose}) {
    const [topics, setTopics] = useState([])
    const [values, setValues] = useState({
        topic: '',
        description: '',
        subject: subject?.subject || '',
        subject_id: subject?.id || '',
        username: username || '',
    })
    const [error, setError] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedMaterialId, setGeneratedMaterialId] = useState(null);
    const [hasCreatedQuestions, setHasCreatedQuestions] = useState(false);

    // Maybe used in the future to get question separately, or ViewMaterial.jsx requires it
    const [generatedQuestionId, setGeneratedQuestionId] = useState(null);

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
        axios.post('/api/llm/ppt/create', values, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        .then(function (response) {
            console.log(`User added successfully: ${response.data}`);
            
            const sid = response.data?.data?.sid;

            if (sid) {
                console.log(`PPT task created with sid: ${sid}`);
                pollPptProgress(sid);
            }

            setValues({
                topic: '',
                instruction: '',
                subject: subject?.subject || '',
                subject_id: subject?.id || '',
                username: username || '',
            })
            //if (onClose) onClose();
        })
        .catch(function (error) {
            console.log(`Error send material generation parameters: ${error}`);
            setError("Failed to generation material. Please try again.");
        })
    }

    useEffect(() => {
        // set subject name to current subject once detected
        setTopics(subject.topics || ["undefined"]);
        setValues(prev => ({...prev, subject: subject.subject}))
    }, [subject])

    // Function to poll the PPT generation progress
    const pollPptProgress = (sid) => {
        const maxAttempts = 60; // e.g., poll for up to 60 times
        let attempts = 0;

        const checkProgress = () => {
            if (attempts>=maxAttempts) {
                console.log("PPT generation timed out. Please try again later.");
                setIsGenerating(false);
                return;
            }

            // use 38c772f66e04402882c520f0ec1fc5c7 for local testing to replace ${sid}
            axios.get(`/api/llm/ppt/progress?sid=38c772f66e04402882c520f0ec1fc5c7`)
            .then( (response) => {
                const data = response.data?.data || {};
                const status = data.pptStatus
                
                console.log(`PPT progress: ${status} (attempt ${attempts + 1}/${maxAttempts})`);

                if (status === 'done') {
                    console.log("PPT generation completed!");
                    console.log("Generated material:", data.material);
                    setError(null);
                    setGeneratedMaterialId(data.material);
                    generateQuestions();
                    //if (onClose) onClose();
                } else if (status === 'failed') {
                    setError('PPT generation failed. Please try again.');
                    console.log("PPT generation failed.");
                    setIsGenerating(false);
                } else {
                    attempts += 1;
                    setTimeout(checkProgress, 5000); // Poll every 5 seconds
                }
            })
            .catch( (error) => {
                console.log(`Error checking progress: ${error}`);
                setError('Error checking generation progress.');
            })
        }
        checkProgress();
    }

    // function for question generation
    const generateQuestions = () => {

        const questionData = {
            ...values,
            material_id: generatedMaterialId
        }
        axios.post('/api/ai/generate-question', questionData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        .then( (response) => {
            const data = response.data;
            console.log(`Question generation request sent successfully: ${data}`);
            setGeneratedQuestionId(data._id);
            setHasCreatedQuestions(true);
        })
        .catch( (error) => {
            console.log(`Error sending question generation request: ${error}`);
            setError("Failed to send question generation request.");
        })
        .finally(() =>
            setIsGenerating(false)
        )
    }

    if (!subject) {
        return <div>Loading Topics...</div>;
    }

    return (
        <div className="user-upload-section">
            {onClose && <button onClick={onClose}>← Back</button>}
            <div className="ai-generator">
                <h3>Your Generated </h3>
                <ul>
                    <li>Select a topic from the dropdown list related to the subject.</li>
                    <li>Optionally, provide specific instructions or requirements for the generated material in the description box.</li>
                    <li>Click the "Generate" button to submit your request.</li>
                    <li>The system will process your request and generate the material based on the provided topic and description.</li>
                </ul>
            </div>
            <form className="ai-generator" onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="topic">Topic</label>
                    {/* Return a list of topics related to the subject */}
                    <select id="topic" name="topic" className="user-input" onChange={(e) => handleChanges(e)} required value={values.topic}>
                        <option className="topic-row" value="">---Choose Topic---</option>
                        {topics.map((topic, index) => (
                            <option key={index} className="topic-row" value={topic}>{topic}</option> 
                        ))}
                    </select>
                    {error && <p className="error-message" style={{color: 'red'}}>{error}</p>}
                    <br/>
                    {/* Textbox to return teacher description/ requirements on the powerpoint */}
                    <textarea 
                        id="description" 
                        name="description" 
                        className="ai-generator"
                        value={values.description}
                        placeholder="Optional instruction for the generated material..."
                        onChange={(e) => handleChanges(e)}
                    />
                </div>
                {console.log(`isGenerating: ${isGenerating}`)}
                <button className={`submit-button ${isGenerating ? 'hovered-disabled' : ''}`} type="submit" disabled={isGenerating}>{isGenerating ? "Generating..." : "Generate"}</button>
            </form>
            <br/>
            <br/>
            <div className="ai-generator" visible={isGenerating}>
                {/**(generatedMaterialId === null && !isGenerating) ? (
                    <p>Your Generated Material will be shown here.</p>
                ) : (generatedMaterial === null && isGenerating) ? (
                    <p>Generating your material, please wait...</p>
                ) : (
                    <ViewMaterial materialId={generatedMaterialId}/>           
                )**/}
                <br/>
                {(generatedMaterialId !== null && hasCreatedQuestions) ? (
                    <ViewQuestion materialId={generatedMaterialId}/> 
                ) : null}
            </div>
        </div>
    );
}

export default GenerateMaterial;