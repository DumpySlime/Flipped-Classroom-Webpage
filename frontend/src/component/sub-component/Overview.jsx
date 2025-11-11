import { useState , useEffect } from 'react';
import axios from 'axios';
import '../../styles.css';
import '../../dashboard.css';

const mockMaterials = [
	{
	id: 1,
	title: 'Algebra Fundamentals',
	type: 'Presentation',
	uploadDate: '2023-11-01'
	},
	{
	id: 2,
	title: 'Probability Basics',
	type: 'Video',
	uploadDate: '2023-10-28'
	},
	{
	id: 3,
	title: 'Statistics Exercise',
	type: 'Worksheet',
	uploadDate: '2023-10-25'
	}
];

function Overview(props) {

    useEffect(() => {
        if (props.activeSection !== 'overview') return;
        // Fetch data if needed
    }, [props.activeSection]);

    return (
        <div className="dashboard-section">
        <h3>Welcome to Your Dashboard</h3>
        <div className="stats-grid">
            <div className="stat-card">
            <h4>Total Students</h4>
            <p>{props.totalStudents}</p>
            </div>
            <div className="stat-card">
            <h4>Materials</h4>
            <p>{props.mockMaterials.length}</p>
            </div>
            <div className="stat-card">
            <h4>Generated Content</h4>
            <p>{props.mockGeneratedContent.length + props.mockGeneratedVideos.length}</p>
            </div>
        </div>
        
        <div className="recent-activity">
            <h4>Recent Activity</h4>
            <div className="activity-list">
            <div className="activity-item">
                <span>Uploaded new presentation</span>
                <span className="activity-time">2 hours ago</span>
            </div>
            <div className="activity-item">
                <span>3 new students enrolled</span>
                <span className="activity-time">Yesterday</span>
            </div>
            <div className="activity-item">
                <span>12 students completed the quiz</span>
                <span className="activity-time">2 days ago</span>
            </div>
            </div>
        </div>
        </div>
    );
}

export default Overview;