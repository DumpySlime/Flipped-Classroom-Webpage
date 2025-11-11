import { useState , useEffect } from 'react';
import axios from 'axios';
import '../../styles.css';
import '../../dashboard.css';

function StudentAnalytics(props) {

    useEffect(() => {
        if (props.activeSection !== 'student-analytics') return;
        // Fetch data if needed
    }, [props.activeSection]);

    return (
        <div className="students-section">
        <div className="section-header">
            <h3>Student Analytics</h3>
        </div>
        <div className="students-list">
            <table className="students-table">
            <thead>
                <tr>
                <th>Student Name</th>
                <th>Progress</th>
                <th>Last Activity</th>
                <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {props.mockStudentProgress.map(student => (
                <tr key={student.id}>
                    <td>{student.name}</td>
                    <td>
                    <div className="student-progress">
                        <div 
                        className="progress-fill" 
                        style={{ width: `${student.progress}%` }}
                        ></div>
                        <span>{student.progress}%</span>
                    </div>
                    </td>
                    <td>{student.lastActivity}</td>
                    <td>
                    <button className="view-details-button">Details</button>
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        </div>
        </div>
    )
}

export default StudentAnalytics;