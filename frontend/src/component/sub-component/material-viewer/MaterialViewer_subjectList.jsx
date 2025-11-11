import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';

function MaterialViewer_subjectList(props) {

    return (
        <div className="materials-section">
        <div className="section-header">
            <h3>Teaching Materials</h3>
            <button className="upload-button">Upload Material</button>
        </div>
        <div className="materials-list">
            {props.mockMaterials.map(material => (
            <div key={material.id} className="material-card">
                <div className="material-info">
                <h4>{material.title}</h4>
                <p>{material.type}</p>
                </div>
                <div className="material-date">
                {material.uploadDate}
                </div>
                <div className="material-actions">
                <button className="download-button">Download</button>
                <button className="delete-button">Delete</button>
                </div>
            </div>
            ))}
        </div>
        </div>
    )
}

export default MaterialViewer_subjectList;