import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';

import FileUpload from './FileUpload.jsx'

function UploadMaterial ({subject, onClose}) {
    const [file, setFile] = useState(null)
    const [topics, setTopics] = useState([])
    const [values, setValues] = useState({
        topic: '',
        subject_id: subject?.id || '',
    })

    const handleFileChange = (slides) => {
        setFile(slides);
    }

    const handleChanges = (e) => {
        setValues({...values, [e.target.name]: e.target.value })
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('topic', values.topic);
        formData.append('subject_id', subject.id);

        console.log('Uploading file:', file.name);

        axios.post('/db/material-add', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        .then(function (response) {
            console.log(`Material added successfully: ${response.data}`);
            setValues({
                topic: '',
                subject_id: subject.id,
            });
            setFile(null);
            if (onClose) onClose();
        })
        .catch(function (error) {
            console.log(`Error adding material: ${error}`);            
            alert('Failed to upload material: ' + (error.response?.data?.error || error.message));
        });
    }

    useEffect(() => {
        setTopics(subject.topics || ["undefined"]);
        setValues(prev => ({...prev, subject_id: subject.id}));
    }, [subject]);

    if (!subject) {
        return <div>Loading Topics...</div>;
    }

    return (
        <div className="user-upload-section">
            {onClose && <button onClick={onClose}>← Back</button>}
            <form className="user-form" onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="topic">Topic</label>
                    {/* Return a list of topics related to the subject */}
                    <select id="topic" name="topic" className="user-input" onChange={(e) => handleChanges(e)} required value={values.topic}>
                        <option className="topic-row">---Choose Topic---</option>
                        {topics.map((topic, index) => (
                            <option key={index} className="topic-row" value={topic}>{topic}</option> 
                        ))}
                    </select>
                </div>
                <div className="form-group">
                    <FileUpload 
                        name="pptxFile" 
                        max_file_size_in_kb="20480" 
                        dataChanger={handleFileChange} 
                        required 
                        allowed_extensions={['ppt', 'pptx']} 
                    /> 
                </div>
                <button className="submit-button" type="submit">Upload</button>
            </form>
        </div>
    );
}

export default UploadMaterial;