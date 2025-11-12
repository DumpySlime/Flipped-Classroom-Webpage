import { useState, useEffect } from 'react';
import '../styles.css';
import '../dashboard.css';

import Overview from './sub-component/Overview';
import AddUser from './sub-component/AddUser';
import MaterialGenerator from './sub-component/material-generator/MaterialGenerator';
import MaterialViewer from './sub-component/material-viewer/MaterialViewer';
import AddSubject from './sub-component/AddSubject';
import StudentAnalytics from './sub-component/StudentAnalytics';
import Assignment from './sub-component/Assignment';

function Dashboard(props) {
const [activeSection, setActiveSection] = useState('overview');
const [roleSections, setRoleSections] = useState({});
const [currentUserInfo, setCurrentUserInfo] = useState({});

// Mock data for demonstration
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

const mockGeneratedVideos = [
	{
	id: 1,
	title: 'Quadratic Formula Explained',
	duration: '8:32',
	generationDate: '2023-11-09',
	thumbnailUrl: '/placeholder-thumbnail.png'
	},
	{
	id: 2,
	title: 'Triangle Properties & Types',
	duration: '12:45',
	generationDate: '2023-11-07',
	thumbnailUrl: '/placeholder-thumbnail.png'
	},
	{
	id: 3,
	title: 'Linear Functions Graphing',
	duration: '15:20',
	generationDate: '2023-11-05',
	thumbnailUrl: '/placeholder-thumbnail.png'
	}
];

const mockGeneratedContent = [
	{
	id: 1,
	title: 'Trigonometry Notes',
	type: 'Notes',
	generationDate: '2023-11-10',
	wordCount: '1,240'
	},
	{
	id: 2,
	title: 'Geometry Quiz',
	type: 'Quiz',
	generationDate: '2023-11-08',
	questionCount: '15'
	},
	{
	id: 3,
	title: 'Calculus Worksheet',
	type: 'Worksheet',
	generationDate: '2023-11-06',
	problemCount: '8'
	}
];

// Mock data for assignments
const mockStudentProgress = [
	{
	id: 1,
	name: 'Alice Johnson',
	progress: 85,
	lastActivity: '2023-11-10 14:30'
	},
	{
	id: 2,
	name: 'Bob Smith',
	progress: 62,
	lastActivity: '2023-11-09 09:15'
	},
	{
	id: 3,
	name: 'Charlie Davis',
	progress: 93,
	lastActivity: '2023-11-10 16:45'
	},
	{
	id: 4,
	name: 'Diana Wilson',
	progress: 48,
	lastActivity: '2023-11-08 11:20'
	}
];

// Mock data for assignments
const mockAssignments = [
	{
	id: 1,
	title: 'Quadratic Equations',
	description: 'Understanding and solving quadratic equations using various methods',
	dueDate: '2025-11-15',
	assignedStudents: ['Alice Johnson', 'Bob Smith', 'Charlie Davis'],
	status: 'Assigned'
	},
	{
	id: 2,
	title: 'Trigonometric Functions',
	description: 'Basic trigonometric functions and their applications',
	dueDate: '2025-11-12',
	assignedStudents: ['Alice Johnson', 'Diana Wilson'],
	status: 'Assigned'
	},
	{
	id: 3,
	title: 'Linear Functions',
	description: 'Graphing and analyzing linear functions',
	dueDate: '2025-11-20',
	assignedStudents: ['Bob Smith', 'Charlie Davis', 'Diana Wilson'],
	status: 'Assigned'
	}
];

// Total students count (previously derived from courses)
const totalStudents = 35;

/*
const renderContentGeneratorSection = () => (
	<div className="content-generator-section">
	<h3>Content Generator</h3>
	
	<div className="ai-generator">
		<div className="form-group">
		<label htmlFor="content-type-select">Content Type</label>
		<select id="content-type-select" className="content-type-select">
			<option value="">-- Choose content type --</option>
			<option value="notes">Notes</option>
			<option value="quiz">Quiz</option>
			<option value="worksheet">Worksheet</option>
			<option value="presentation">Presentation</option>
		</select>
		</div>
		
		<div className="form-group">
		<label htmlFor="content-topic-input">Content Topic</label>
		<input
			type="text"
			id="content-topic-input"
			placeholder="Enter content topic"
			className="topic-input"
		/>
		</div>
		
		<div className="form-group">
		<label htmlFor="content-instructions-input">Additional Instructions</label>
		<textarea
			id="content-instructions-input"
			placeholder="Provide more details for the AI content generation..."
			rows="4"
			className="instructions-input"
		></textarea>
		</div>
		
		<button 
		onClick={() => handleGenerateMaterial('content')}
		className="generate-button"
		disabled={loading}
		>
		{loading ? 'Generating Content...' : 'Generate Content'}
		</button>
		
		{message2 && (
		<div className={`message ${message2.includes('success') ? 'success' : 'error'}`}>
			{message2}
		</div>
		)}
	</div>
	
	<div className="generated-content">
		<h4>Your AI-generated Educational Content</h4>
		<div className="content-list">
		{mockGeneratedContent.map(content => (
			<div key={content.id} className="content-card">
			<div className="content-info">
				<h5>{content.title}</h5>
				<p>{content.type}</p>
				<p className="content-date">Generated on {content.generationDate}</p>
				{content.wordCount && <p>Word Count: {content.wordCount}</p>}
				{content.questionCount && <p>Questions: {content.questionCount}</p>}
				{content.problemCount && <p>Problems: {content.problemCount}</p>}
			</div>
			<div className="content-actions">
				<button className="view-button">View</button>
				<button className="download-button">Download</button>
			</div>
			</div>
		))}
		</div>
	</div>
	
	<div className="content-templates">
		<h4>Content Templates</h4>
		<p className="templates-description">Quick-start templates for common teaching materials</p>
		<div className="templates-list">
		<div className="template-card">
			<h5>Lecture Notes</h5>
			<p>Comprehensive notes with key points and explanations</p>
			<button className="use-template-button">Use Template</button>
		</div>
		<div className="template-card">
			<h5>Multiple Choice Quiz</h5>
			<p>Assessment with multiple choice questions</p>
			<button className="use-template-button">Use Template</button>
		</div>
		<div className="template-card">
			<h5>Practice Worksheet</h5>
			<p>Exercises for students to apply concepts</p>
			<button className="use-template-button">Use Template</button>
		</div>
		<div className="template-card">
			<h5>Presentation Outline</h5>
			<p>Structure for effective classroom presentations</p>
			<button className="use-template-button">Use Template</button>
		</div>
		</div>
	</div>
	</div>
);
*/

const allowedSectionsByRole = {
	student: {
		overview: 'Overview',
		materials: 'Materials',
		assignments: 'Assignments',
		'student-analytics': 'Student Analytics'
	},
	teacher: {
		overview: 'Overview',
		materials: 'Materials',
		assignments: 'Assignments',
		'student-analytics': 'Student Analytics',
		'material-generation': 'Material Generation'
	},
	admin: {
		overview: 'Overview',
		materials: 'Materials',
		assignments: 'Assignments',
		'student-analytics': 'Student Analytics',
		'material-generation': 'Material Generation',
		'add-subject': 'Add Subject',
		'add-user': 'Add User'
	}
};

const renderContent = () => {

	if (activeSection === 'overview') return <Overview activeSection={activeSection} totalStudents={totalStudents} mockMaterials={mockMaterials} mockGeneratedContent={mockGeneratedContent} mockGeneratedVideos={mockGeneratedVideos}/>;
	if (activeSection === 'materials') return <MaterialViewer activeSection={activeSection} userInfo={props.userInfo} userRole={props.userRole} mockMaterials={mockMaterials}/>;
	if (activeSection === 'material-generation') return <MaterialGenerator activeSection={activeSection} />;
	if (activeSection === 'student-analytics') return <StudentAnalytics activeSection={activeSection} mockStudentProgress={mockStudentProgress}/>;
	if (activeSection === 'assignments') return <Assignment activeSection={activeSection} mockAssignments={mockAssignments} mockStudentProgress={mockStudentProgress}/>;
	if (activeSection === 'add-subject') return <AddSubject activeSection={activeSection} />;
	if (activeSection === 'add-user') return <AddUser setActiveSection={setActiveSection} />;
	return <Overview activeSection={activeSection} totalStudents={totalStudents} mockMaterials={mockMaterials} mockGeneratedContent={mockGeneratedContent} mockGeneratedVideos={mockGeneratedVideos}/>;
};
	
useEffect(() => {
	setRoleSections(allowedSectionsByRole[props.userRole]);
	setCurrentUserInfo(props.userInfo);
}, [props.userRole]);

return (
	<div className="dashboard">
	<header className="dashboard-header">
		<div className="header-left">
		<h2>Admin Dashboard</h2>
		<div className="admin-welcome">
			{currentUserInfo.firstName && currentUserInfo.lastName ? (
				<>Welcome, {currentUserInfo.firstName} {currentUserInfo.lastName}! You have successfully logged in.</>
			) : (
				<>ERROR</>
			)}
		</div>
		</div>
		<div className="header-right">
		<button onClick={props.onLogout} className="logout-button">
			Logout
		</button>
		</div>
	</header>
	
	<div className="dashboard-content">
		<nav className="dashboard-sidebar">
		<ul className="sidebar-menu">
			{/* Render dynamic tabs based on role */}
			{
				Object.entries(roleSections).map(([key, label]) => (
					<li 
					key={key}
					className={activeSection === key ? 'active' : ''}
					onClick={() => setActiveSection(key)}
					>
					<span> {label} </span>
					</li>
				))
			}
		</ul>
		</nav>
		
		<main className="dashboard-main">
		{renderContent()}
		</main>
	</div>
	</div>
);
}

export default Dashboard;