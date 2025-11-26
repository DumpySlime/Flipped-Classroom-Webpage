import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';

function GenerateMaterial({subject, onClose}) {
    const [topics, setTopics] = useState([])
    const [values, setValues] = useState({
        topic: '',
        description: '',
        subject: subject?.subject || '',
        subject_id: subject?.id || '',
    })

    const handleChanges = (e) => {
        setValues({...values, [e.target.name]: e.target.value })
    }

    const handleSubmit = (e) => {
        e.preventDefault();

        console.log('Form submitted with values:', values);
        axios.post('/llm/api/query/material', values, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        .then(function (response) {
            console.log(`User added successfully: ${response.data}`);
            setValues({
                topic: '',
                instruction: '',
                subject: subject?.subject || '',
                subject_id: subject?.id || '',
            })
            if (onClose) onClose();
        })
        .catch(function (error) {
            console.log(`Error send material generation parameters: ${error}`);
        });
    }

    useEffect(() => {
        {/* set subject name to current subject once detected */}
        setTopics(subject.topics || ["undefined"]);
        setValues(prev => ({...prev, subject: subject.subject}))
    }, [subject])

    if (!subject) {
        return <div>Loading Topics...</div>;
    }

    return (
        <div className="user-upload-section">
            {onClose && <button onClick={onClose}>← Back</button>}
            <form className="ai-generator" onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="topic">Topic</label>
                    {/* Return a list of topics related to the subject */}
                    <select id="topic" name="topic" className="user-input" onChange={(e) => handleChanges(e)} required value={values.topic}>
                        <option className="topic-row">---Choose Topic---</option>
                        {topics.map((topic, index) => (
                            <option key={index} className="topic-row" value={topic}>{topic}</option> 
                        ))}
                    </select>
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
                <button className="submit-button" type="submit">Generate</button>
            </form>
            <br/>
            <br/>
            <div className="ai-generator">
                <h3>Your Generated </h3>
                <ul>
                    <li>Select a topic from the dropdown list related to the subject.</li>
                    <li>Optionally, provide specific instructions or requirements for the generated material in the description box.</li>
                    <li>Click the "Generate" button to submit your request.</li>
                    <li>The system will process your request and generate the material based on the provided topic and description.</li>
                </ul>
            </div>
        </div>
    );
}

export default GenerateMaterial;