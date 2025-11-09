import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';

function MaterialViewer({ activeSection }) {
    const [materials, setMaterials] = useState([]);

    const [error, setError] = useState(null);

    useEffect(() => {
        if (activeSection !== 'material-viewer') return;
        const ac = new AbortController();
        
        console.log('Fetching Materials...')
        (() => {
            setError(null);
            const user = localStorage.getItem('user');
            let user_id = null;
            if (user) {
            const user = JSON.parse(user);
                user_id = user._id; 
            }
            axios.get('/db/materials', {
                params: {
                    uploaded_by: user_id
                }
            })
            .then(function (response) {
                console.log(`response: ${response}`)
                const data = response.data;
                console.log(`Fetched material data: ${data}`)
                const mat_list = (data.materials || []).map(m => ({
                    mat_id: m.id,
                    filename: m.filename,
                    subject: m.subject,
                    topic: m.topic,
                    upload_date: m.upload_date
                }));
                setMaterials(mat_list);
            })
            .catch(function (error) {
                if (error.name !== 'AbortError') setError('Failed to load teachers');
            })
        })();
        return () => ac.abort();
    }, [activeSection]);

    return (
        <div className="materials-section">
        <div className="section-header">
            <h3>Materials</h3>
            <button className="upload-button">Upload Material</button>
        </div>
        <div className="materials-list">
            {materials.map(m => (
            <div key={m.id} className="material-card">
                <div className="material-info">
                <h4>{m.topic}</h4>
                <p>{m.filename}</p>
                </div>
                <div className="material-date">
                {m.upload_date}
                </div>
                <div className="material-actions">
                <button className="download-button">Download</button>
                <button className="delete-button">Delete</button>
                </div>
            </div>
            ))}
        </div>
        </div>
    );
}
export default MaterialViewer;