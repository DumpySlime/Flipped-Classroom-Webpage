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
        axios.delete('/db/material-delete?material_id=' + matId, {
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
                username={props.userInfo.username}
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
            {props.userRole !== 'student' && (
                <button className="button primary" onClick={() => setShowGenerate(true)}>
                Generate Material
                </button>
            )}
            </div>

            <div className="materials-list">
            {materials.map((m) => (
                <div 
                key={m.id} 
                className="material-row" 
                onClick={() => handleViewMaterial(m)}
                >
                <div className="material-main">
                    <div className="material-topic">{m.topic}</div>
                    <div className="material-meta">
                    <span className="material-date">
                        {m.created_at}
                    </span>
                    </div>
                </div>

                {props.userRole !== 'student' && (
                    <div className="material-actions">
                    <button
                        className="button subtle"
                        onClick={(e) => {
                        e.stopPropagation();
                        console.log('Editing material id:', m.id);
                        handleEditMaterial(m);
                        }}
                    >
                        Edit
                    </button>
                    <button
                        className="button danger subtle"
                        onClick={(e) => {
                        e.stopPropagation();
                        console.log('Deleting material id:', m.id);
                        deleteMaterial(m.id);
                        }}
                    >
                        Delete
                    </button>
                    </div>
                )}
                </div>
            ))}
            {materials.length === 0 && (
                <div className="materials-empty">
                No materials yet.
                </div>
            )}
            </div>
        </div>
    );

}
export default MaterialList;