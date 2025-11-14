import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';

import UploadMaterial from './UploadMaterial';
import EditMaterial from './EditMaterial';
import ViewMaterial from './ViewMaterial';
import GenerateMaterial from './GenerateMaterial';

function MaterialList(props) {
    const [materials, setMaterials] = useState([]);    
    const [showUpload, setShowUpload] = useState(false);
    const [showEdit, setShowEdit] = useState(false);
    const [showView, setShowView] = useState(false);
    const [showGenerate, setShowGenerate] = useState(false);
    const [selectedMaterial, setSelectedMaterial] = useState(null);

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

    function handleViewMaterial(material) {
        setSelectedMaterial(material);
        setShowView(true);
    }

    function handleEditMaterial(material) {
        setSelectedMaterial(material);
        setShowEdit(true);
    }

    useEffect(() => {
        setMaterials(props.materials);
    }, [props.materials, props.subject]);

    // If showing upload
    if (showUpload) {
        return (
            <UploadMaterial 
                subject={props.subject}
                onClose={() => setShowUpload(false)}
            />
        );
    }

    // If showing generate
    if (showGenerate) {
        return (
            <GenerateMaterial            
                subject={props.subject}
                onClose={() => setShowGenerate(false)}
            />
        )
    }

    // If showing view
    if (showView && selectedMaterial) {
        return (
            <ViewMaterial 
                material={selectedMaterial} 
                onClose={() => setShowView(false)}
            />
        );
    }

    // If showing edit
    if (showEdit && selectedMaterial) {
        return (
            <EditMaterial 
                material={selectedMaterial} 
                onClose={() => setShowEdit(false)}
            />
        );
    }

    return (
        <div className="materials-section">
        <div className="section-header">
            <h3>{props.subject.subject} Materials</h3>
            {/* disable upload button if role = student */}
            {
                (props.userRole !== "student") ? (
                    <>
                    <button className="button" onClick={() => setShowUpload(true)}>Upload Material</button> 
                    <button className="button" onClick={() => setShowGenerate(true)}>Generate Material</button> 
                    </>
                ) : null
            }
        </div>
        <div className="materials-list">
            {
                materials.map(m => (
                    <div key={m.id} className="material-card" onClick={() => handleViewMaterial(m)}>
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
                                <button className="button" onClick={(e) => {
                                    e.stopPropagation(); 
                                    deleteMaterial(m.id);
                                }}>Delete</button>
                                <button className="button" onClick={(e) => {
                                    e.stopPropagation(); 
                                    handleEditMaterial(m)
                                }}>Edit</button>
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