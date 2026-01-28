import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';

import UploadMaterial from './UploadMaterial';
import EditMaterial from './EditMaterial';
import ViewMaterial from './ViewMaterial';
import GenerateMaterial from './GenerateMaterial';
import { materialAPI } from '../../../services/api';

function MaterialList(props) {
    const [materials, setMaterials] = useState([]);    
    const [showUpload, setShowUpload] = useState(false);
    const [showEdit, setShowEdit] = useState(false);
    const [showView, setShowView] = useState(false);
    const [showGenerate, setShowGenerate] = useState(false);
    const [selectedMaterial, setSelectedMaterial] = useState(null);

    async function deleteMaterial(matId) {
        try {
            await materialAPI.delete(matId);
            setMaterials(prevMaterials => prevMaterials.filter(material => material.id !== matId));
            alert('Material deleted successfully');
        } catch (error) {
            console.error('Error deleting material:', error);
            alert('Failed to delete material');
        }
    }

    function handleViewMaterial(material) {
        setSelectedMaterial(material);
        setShowView(true);
    }

    function handleEditMaterial(material) {
        setSelectedMaterial(material);
        setShowEdit(true);
    }

    // back navigation
    function handleBackToSubjects() {
        setMaterials([]);
        setSelectedMaterial(null);
        setShowUpload(false);
        setShowEdit(false);
        setShowView(false);
        setShowGenerate(false);
        
        props.onBackToSubjectList();
    }

    useEffect(() => {
        // Safety check for materials prop
        const safeMaterials = Array.isArray(props.materials) ? props.materials : [];
        console.log('MaterialList received materials:', safeMaterials);
        setMaterials(safeMaterials);
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
                username={props.userInfo?.username || 'user'}
                onClose={() => setShowGenerate(false)}
            />
        );
    }

    // If showing view
    if (showView && selectedMaterial) {
        return (
            <ViewMaterial 
                material={selectedMaterial} 
                userInfo={props.userInfo}
                userRole={props.userRole}
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
            {props.subjectLength > 1 && (
            <div className="back-navigation">
                <button 
                onClick={handleBackToSubjects}
                className="back-button"
                aria-label="Back to subjects list"
                >
                ← Back to Subjects
                </button>
            </div>
            )}
            <div className="section-header">
                <h3>{props.subject?.subject || 'Materials'}</h3>
                {props.userRole !== 'student' && (
                    <button className="button primary" onClick={() => setShowGenerate(true)}>
                        Generate Material
                    </button>
                )}
            </div>

            <div className="materials-list">
                {materials.length > 0 ? (
                    materials.map((m) => (
                        <div 
                            key={m.id} 
                            className="material-row" 
                            onClick={() => handleViewMaterial(m)}
                        >
                            <div className="material-main">
                                <div className="material-topic">{m.topic}</div>
                                <div className="material-meta">
                                    <span className="material-date">
                                        {m.created_at 
                                            ? new Date(m.created_at).toLocaleDateString() 
                                            : 'N/A'}
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
                    ))
                ) : (
                    <div className="materials-empty">
                        No materials yet for this subject.
                    </div>
                )}
            </div>
        </div>
    );
}

export default MaterialList;
