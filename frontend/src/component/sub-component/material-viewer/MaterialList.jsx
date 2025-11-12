import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';

import UploadMaterial from './UploadMaterial';
import EditMaterial from './EditMaterial';
import ViewMaterial from './ViewMaterial';

function MaterialList(props) {
    const [materials, setMaterials] = useState([]);

    function deleteMaterial(matId) {
        const ac = new AbortController();
        axios.delete('/material-delete', {
            params: {
                material_id: matId
            }, 
            signal: ac.signal
        })
        .then((response) => {
            setMaterials(prevMaterials => prevMaterials.filter(material => material.id !== matId));
            alert(response.data.message);
        })
        .catch(error => {
            if (error.name !== 'CanceledError') {
                console.error('Error delete materials:', error);
            }
        })
    }

    useEffect(() => {
        if (props.activeSection !== 'material-viewer') return;
        // set materials related to subject
        for (let mat in props.materials) {
            if (mat.subject_id === props.subject.id) {
                setMaterials(prevMaterials => ({...prevMaterials, mat}));
            }
        }
    }, [props.activeSection, props.materials, props.subject.id]);

    return (
        <div className="materials-section">
        <div className="section-header">
            <h3>Materials</h3>
            {/* disable upload button if role = student */}
            {
                (props.userRole !== "student") ? 
                <button className="button" onClick={<UploadMaterial activeSection={props.activeSection}/>}>Upload Material</button> : null
            }
        </div>
        <div className="materials-list">
            {
                materials.map(m => (
                    <div key={m.id} className="material-card" onClick={<ViewMaterial material={m} activeSection={props.activeSection}/>}>
                        <div className="material-info">
                        <h4>{m.topic}</h4>
                        <p>{m.filename}</p>
                        </div>
                        <div className="material-date">
                        {m.upload_date}
                        </div>
                        <div className="material-actions">
                        {
                            (props.userRole !== "student") ? (
                                <>
                                <button className="button" onClick={() => deleteMaterial(m.id)}>Delete</button>
                                <button className="button" onClick={<EditMaterial material={m} activeSection={props.activeSection}/>}>Edit</button>
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