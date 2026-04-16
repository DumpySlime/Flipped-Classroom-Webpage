import { useState, useEffect, useCallback } from 'react';
import React from 'react';
import '../../../styles.css';
import '../../../dashboard.css';

import UploadMaterial from './UploadMaterial';
import EditMaterial from './EditMaterial';
import ViewMaterial from './ViewMaterial';
import GenerateMaterial from './GenerateMaterial';
import { materialAPI } from '../../../services/api';
import { useTranslation } from 'react-i18next';

function MaterialList(props) {
    const { t, i18n } = useTranslation();

    const getText = (value) => {
        if (!value && value !== 0) return '';
        if (typeof value === 'object' && !Array.isArray(value)) {
            const lang = i18n.language?.startsWith('zh') ? 'zh' : 'en';
            return value[lang] ?? value.en ?? value.zh ?? '';
        }
        return String(value);
    };

    const [materials, setMaterials] = useState(
        Array.isArray(props.materials) ? props.materials : []
    );
    const [showUpload, setShowUpload] = useState(false);
    const [showEdit, setShowEdit] = useState(false);
    const [showView, setShowView] = useState(false);
    const [showGenerate, setShowGenerate] = useState(false);
    const [selectedMaterial, setSelectedMaterial] = useState(null);

    // ✅ 只在 subject 改變時 reset（唔覆蓋本地刪除操作）
    useEffect(() => {
        const safeMaterials = Array.isArray(props.materials) ? props.materials : [];
        setMaterials(safeMaterials);
    }, [props.subject]);

    // ✅ 刪除：本地 filter + 通知 parent（如果有 callback）
    const deleteMaterial = useCallback(async (matId) => {
        if (!window.confirm(t('confirmDelete') || 'Delete this material?')) return;
        try {
            await materialAPI.delete(matId);
            setMaterials(prev => prev.filter(m => m.id !== matId));
            // ✅ 通知 parent 更新（如果有傳 callback）
            if (typeof props.onMaterialDeleted === 'function') {
                props.onMaterialDeleted(matId);
            }
        } catch (error) {
            console.error('Error deleting material:', error);
            alert('Failed to delete material, you are not the owner of this material or there is a server error');
        }
    }, [props.onMaterialDeleted, t]);

    const handleViewMaterial = useCallback((material) => {
        setSelectedMaterial(material);
        setShowView(true);
    }, []);

    const handleEditMaterial = useCallback((material) => {
        setSelectedMaterial(material);
        setShowEdit(true);
    }, []);

    // ✅ 安全呼叫 onBackToSubjectList
    const handleBackToSubjects = useCallback(() => {
        setMaterials([]);
        setSelectedMaterial(null);
        setShowUpload(false);
        setShowEdit(false);
        setShowView(false);
        setShowGenerate(false);
        if (typeof props.onBackToSubjectList === 'function') {
            props.onBackToSubjectList();
        }
    }, [props.onBackToSubjectList]);

    if (showUpload) {
        return (
            <UploadMaterial
                subject={props.subject}
                onClose={() => setShowUpload(false)}
            />
        );
    }

    if (showGenerate) {
        return (
            <GenerateMaterial
                subject={props.subject}
                userInfo={props.userInfo}
                userRole={props.userRole}
                onClose={() => setShowGenerate(false)}
            />
        );
    }

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
                        ← {t('backToSubjects')}
                    </button>
                </div>
            )}

            <div className="section-header">
                <h3>{getText(props.subject?.subject) || 'Materials'}</h3>
                {props.userRole !== 'student' && (
                    <button className="button primary" onClick={() => setShowGenerate(true)}>
                        {t('generateMaterial')}
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
                                <div className="material-topic">{getText(m.attribute?.topic)}</div>
                                <div className="material-meta">
                                    {m.attribute?.subtopic?.length > 0 ? (
                                        m.attribute.subtopic.map((sub, idx) => (
                                            <React.Fragment key={idx}>
                                                <span className="material-date">{getText(sub)}</span>
                                                <div></div>
                                            </React.Fragment>
                                        ))
                                    ) : <></>}
                                    <br />
                                    <span className="material-date">
                                        {m.created_at ? new Date(m.created_at).toLocaleDateString() : 'N/A'}
                                    </span>
                                </div>
                            </div>

                            {props.userRole !== 'student' && (
                                <div className="material-actions">
                                    <button
                                        className="button subtle"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleEditMaterial(m);
                                        }}
                                    >
                                        {t('editButton')}
                                    </button>
                                    <button
                                        className="button danger subtle"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteMaterial(m.id);
                                        }}
                                    >
                                        {t('deleteButton')}
                                    </button>
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    <div className="materials-empty">
                        {t('emptyMaterial')}
                    </div>
                )}
            </div>
        </div>
    );
}

export default MaterialList;