import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';

function MaterialList(props) {
    const [materials, setMaterials] = useState([]);

    useEffect(() => {
        if (props.activeSection !== 'material-viewer') return;
        // set materials related to subject
        for (let mat in props.materials) {
            if (mat.subject_id === props.subject.id) {
                setMaterials(prevMaterials => ({...prevMaterials, mat}));
            }
        }
    }, [props.activeSection]);

    return (
        <div className="materials-section">
        <div className="section-header">
            <h3>Materials</h3>
            {/* disable upload button if role = student */}
            {
                (props.userRole !== "student") ? 
                <button className="button" onClick>Upload Material</button> : null
            }
        </div>
        <div className="materials-list">
            {
                materials.map(m => (
                    <div key={m.id} className="material-card">
                        <div className="material-info">
                        <h4>{m.topic}</h4>
                        <p>{m.filename}</p>
                        </div>
                        <div className="material-date">
                        {m.upload_date}
                        </div>
                        <div className="material-actions">
                        <button className="button">Download</button>
                        {
                            (props.userRole !== "student") ? (
                                <>
                                <button className="button">Delete</button>
                                <button className="button">Edit</button>
                                </>
                                ) : null
                        }
                        </div>
                    </div>
                ))
            }
        </div>
        </div>
    );
}
export default MaterialList;