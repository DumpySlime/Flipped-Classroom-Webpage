import { useState, useEffect } from 'react';
import AddUser from './sub-component/AddUser';
import '../styles.css';
import '../dashboard.css';

function AdminDashboard({ userInfo }) {
const [activeSection, setActiveSection] = useState('overview');
const [activeAssignmentSection, setActiveAssignmentSection] = useState('manage');
const [loading, setLoading] = useState(false);
const [message, setMessage] = useState('');
const [message2, setMessage2] = useState('');

// Default mock data in case userInfo is not available
const adminData = userInfo || {
	firstName: 'Dr.',
	lastName: 'Johnson',
	role: 'admin'
};
	
	// Mock data for demonstration
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

// Total students count (previously derived from courses)
const totalStudents = 35;

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

const handleLogout = () => {
	localStorage.removeItem('token');
	window.location.href = '/';
};

const handleGenerateMaterial = async (type) => {
	setLoading(true);
	if (type === 'video') {
	setMessage('');
	try {
		// In a real application, this would be an API call to the backend
		// Simulating API call with timeout
		await new Promise(resolve => setTimeout(resolve, 1500));
		setMessage('Video generated successfully!');
	} catch (error) {
		setMessage('Failed to generate video. Please try again.');
		console.error('Error generating video:', error);
	} finally {
		setLoading(false);
	}
	} else {
	setMessage2('');
	try {
		// In a real application, this would be an API call to the backend
		// Simulating API call with timeout
		await new Promise(resolve => setTimeout(resolve, 1500));
		setMessage2('Content generated successfully!');
	} catch (error) {
		setMessage2('Failed to generate content. Please try again.');
		console.error('Error generating content:', error);
	} finally {
		setLoading(false);
	}
	}
};

const renderOverviewSection = () => (
	<div className="dashboard-section">
	<h3>Welcome to Your Dashboard</h3>
	<div className="stats-grid">
		<div className="stat-card">
		<h4>Total Students</h4>
		<p>{totalStudents}</p>
		</div>
		<div className="stat-card">
		<h4>Materials</h4>
		<p>{mockMaterials.length}</p>
		</div>
		<div className="stat-card">
		<h4>Generated Content</h4>
		<p>{mockGeneratedContent.length + mockGeneratedVideos.length}</p>
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

const renderMaterialsSection = () => (
	<div className="materials-section">
	<div className="section-header">
		<h3>Teaching Materials</h3>
		<button className="upload-button">Upload Material</button>
	</div>
	<div className="materials-list">
		{mockMaterials.map(material => (
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
);

const renderStudentsSection = () => (
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
			{mockStudentProgress.map(student => (
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
);

function renderMaterialGenerationSection() {
	return (
	<div className="material-generation-section">
		<h3>Material Generation</h3>

		<div className="ai-generator">

		<div className="form-group">
			<label htmlFor="material-topic-input">Material Topic</label>
			<input
			type="text"
			id="material-topic-input"
			placeholder="Enter material topic"
			className="topic-input" />
		</div>

		<div className="form-group">
			<label htmlFor="material-subject-select">Material Subject</label>
			<select id="material-subject-select"></select>
		</div>
		
		<div className="form-group">
			<label htmlFor="material-instructions-input">Additional Instructions</label>
			<textarea
			id="material-instructions-input"
			placeholder="Provide more details for the AI material generation..."
			rows="4"
			className="instructions-input"
			></textarea>
		</div>

		<button
			onClick={() => handleGenerateMaterial('video')}
			className="generate-button"
			disabled={loading}
		>
			{loading ? 'Generating Video...' : 'Generate Video'}
		</button>

		{message && (
			<div className={`message ${message.includes('success') ? 'success' : 'error'}`}>
			{message}
			</div>
		)}
		</div>

		<div className="recent-videos">
		<h4>Recently Generated Videos</h4>
		<div className="videos-list">
			{mockGeneratedVideos.map(video => (
			<div key={video.id} className="video-card">
				<div className="video-thumbnail">
				<img src={video.thumbnailUrl} alt={video.title} />
				<span className="video-duration">{video.duration}</span>
				</div>
				<div className="video-info">
				<h5>{video.title}</h5>
				<p className="video-date">Generated on {video.generationDate}</p>
				</div>
				<div className="video-actions">
				<button className="view-button">View</button>
				<button className="download-button">Download</button>
				</div>
			</div>
			))}
		</div>
		</div>

		<div className="video-templates">
		<h4>Video Templates</h4>
		<div className="templates-list">
			<div className="template-card">
			<h5>Lecture Introduction</h5>
			<p>Perfect for starting a new topic with key concepts</p>
			<button className="use-template-button">Use Template</button>
			</div>
			<div className="template-card">
			<h5>Concept Explainer</h5>
			<p>Ideal for breaking down complex ideas</p>
			<button className="use-template-button">Use Template</button>
			</div>
			<div className="template-card">
			<h5>Problem Solving Walkthrough</h5>
			<p>Step-by-step solution demonstration</p>
			<button className="use-template-button">Use Template</button>
			</div>
		</div>
		</div>
	</div>
	);
}

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

// create subject rendering
const [allTeachers, setAllTeachers] = useState([]);
const [selectedTeacherIds, setSelectedTeacherIds] = useState([]);
const [activeTabId, setActiveTabId] = useState(null);

const [loadingTeachers, setLoadingTeachers] = useState(false);
const [error, setError] = useState(null);

useEffect(() => {
	if (activeSection !== 'add-subject') return;
	const ac = new AbortController();

	console.log('Fetching teachers for subject creation...');
	(async () => {
	try {
		setLoadingTeachers(true);
		setError(null);
		const res = await fetch('/db/user?role=teacher');
		const data = await res.json();
		console.log('Fetched teacher data:', data);
		const list = (data.users || []).map(t => ({
		id: t.id,
		name: t.username
		}));
		setAllTeachers(list);
		const ids = list.map(t => t.id);
		setSelectedTeacherIds(ids);
		if (ids.length) setActiveTabId(ids[0]);
	} catch (e) {
		if (e.name !== 'AbortError') setError('Failed to load teachers');
	} finally {
		setLoadingTeachers(false);
	}
	})();
	return () => ac.abort();
}, [activeSection]);

// create buttons for + - subjects
const [topics, setTopics] = useState(['']);

const addTopic = () => {
	setTopics(topics => [...topics, '']);
}

const updateTopic = (idx, value) => {
	setTopics(prev => {
	const copy = [...prev];
	copy[idx] = value;
	return copy;
	});
};

const removeTopic = (idx) => {
	setTopics(prev => prev.filter((_, i) => i !== idx));
};

// add subject button
const handleSubmitSubject = async() => {
	const subjectName = (document.getElementById('subject-input')?.value || '').trim();
	
	if (!subjectName) {
		alert('Please enter a subject name');
		return;
	}
	if (!topics.some(topic => topic.trim())) {
		alert('Please add at least one topic');
		return;
	}
	if (!selectedTeacherIds.length) {
		alert('Please select at least one teacher');
		return;
	}

	const payload = {
		subject: subjectName,
		topics: topics.filter(t => t.trim().length > 0),
		teachers: selectedTeacherIds
	}

	try {
		const response = await fetch('/admin/api/subject/add', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(payload)
		});

		const data = await response.json();
		console.log('Subject creation response:', data);
		if (response.ok) {
			alert(`Success! Subject created:\n${JSON.stringify(data, null, 2)}`);
			// Navigate to dashboard
			setActiveSection('dashboard');
		} else {
			throw new Error(data.error || 'Failed to create subject');
		}
	} catch (error) {
		alert(`Error: ${error.message}`);
	}
}

const renderSubjectCreationSection = () => (
	<div className="subject-creation-section">
	<h3>Subject Creation</h3>
	<form className="subject-form">
		<div className="form-group">
		<label htmlFor="subject-input">Subject Name</label>
		<input
			type="text"
			id="subject-input"
			name="subject"
			className="subject-input"
			placeholder="Enter subject name"
		/>
		</div>

		<div className="form-group">
		<label htmlFor="topic-input">Topic Name</label>
		{/* Render dynamic topic inputs */}
		{topics.map((topic, index) => (
			<div key={`topic-${index}`} className="topic-input-row">
			<input
				type="text"
				id={`topic-input-${index}`}
				name={`topic-${index}`}
				placeholder={`Enter topic name ${index + 1}`}
				value={topic}
				className="topic-input"
				onChange={(e) => updateTopic(index, e.target.value)}
			/>
			{topic.length > 1 && (
				<button
				type="button"
				onClick={() => removeTopic(index)}
				className="remove-button"
				aria-label={`Remove topic ${index + 1}`}
				>
				-
				</button>
			)}
			</div>
		))}
		<button 
			type="button"
			className="add-button"
			aria-label="Add topic"
			onClick={addTopic}>
			+
		</button>  
		</div>   
		
		<div className="form-group">
		<label htmlFor="teacher-input">Teachers</label>
		<div className="form-group">
			{loadingTeachers && <p> Loading teachers...</p>}
			{error && <p>{error}</p>}

			{!loadingTeachers && !error && (
			<div className="teacher-tabs">
				{allTeachers.map(t => {
				const tid = t.id;
				const isSelected = selectedTeacherIds.includes(tid);
				const isActive = activeTabId === tid;
				return (
					<button
					key={tid}
					type="button" 
					id={`teacher-tab-${tid}`}
					name={`teacher-${tid}-${t.name}`}
					className={`teacher-tab ${isSelected ? 'selected' : ''} ${isActive ? 'active' : ''}`}
					title={t.name}
					onClick={() => {
						setSelectedTeacherIds(prev => prev.includes(tid) ? prev.filter(id => id !== tid) : [...prev, tid]);
						setActiveTabId(tid);
					}}
					>
					{t.name}
					</button>
				)
				})}
			</div>
			)}
		</div>
		</div>

		<div className="add-material-button">
		<button type="button" className="create-button" onClick={handleSubmitSubject}>
			Submit
		</button>
		</div>
	</form>
	</div>
);

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

// State for new assignment form
const [newAssignment, setNewAssignment] = useState({
	title: '',
	description: '',
	dueDate: '',
	selectedStudents: []
});

const [showStudentDropdown, setShowStudentDropdown] = useState(false);

// Handle assignment creation
const handleCreateAssignment = () => {
	if (newAssignment.title && newAssignment.dueDate && newAssignment.selectedStudents.length > 0) {
	// In a real app, this would be an API call
	alert('Assignment created successfully!');
	// Reset form
	setNewAssignment({ title: '', description: '', dueDate: '', selectedStudents: [] });
	} else {
	alert('Please fill in all required fields and select at least one student.');
	}
};

const renderAssignmentsSection = () => (
	<div className="assignments-section">
	<div className="section-header">
		<h3>Assignments</h3>
	</div>
	
	{/* Assignment Section Tabs */}
	<div className="assignment-tabs">
		<button 
		className={`tab-button ${activeAssignmentSection === 'manage' ? 'active' : ''}`}
		onClick={() => setActiveAssignmentSection('manage')}
		>
		Manage Assignments
		</button>
		<button 
		className={`tab-button ${activeAssignmentSection === 'current' ? 'active' : ''}`}
		onClick={() => setActiveAssignmentSection('current')}
		>
		Current Assignments
		</button>
	</div>
	
	{/* Conditional Content Based on Selected Tab */}
	{activeAssignmentSection === 'manage' && (
		<div className="create-assignment-form">
		<h4>Create New Assignment</h4>
		
		<div className="form-group">
			<label htmlFor="assignment-title">Title *</label>
			<input
			type="text"
			id="assignment-title"
			value={newAssignment.title}
			onChange={(e) => setNewAssignment({...newAssignment, title: e.target.value})}
			placeholder="Enter assignment title"
			className="assignment-input"
			/>
		</div>
		
		<div className="form-group">
			<label htmlFor="assignment-description">Description</label>
			<textarea
			id="assignment-description"
			value={newAssignment.description}
			onChange={(e) => setNewAssignment({...newAssignment, description: e.target.value})}
			placeholder="Enter assignment description"
			rows="3"
			className="assignment-textarea"
			></textarea>
		</div>
		
		<div className="form-group">
			<label htmlFor="assignment-due-date">Due Date *</label>
			<input
			type="date"
			id="assignment-due-date"
			value={newAssignment.dueDate}
			onChange={(e) => setNewAssignment({...newAssignment, dueDate: e.target.value})}
			className="assignment-date"
			/>
		</div>
		
		<div className="form-group">
			<label htmlFor="custom-student-select">Select Students *</label>
			<div className="custom-multiselect">
			<div 
				className="multiselect-trigger"
				onClick={() => setShowStudentDropdown(!showStudentDropdown)}
			>
				<span>
				{newAssignment.selectedStudents.length > 0 
					? `${newAssignment.selectedStudents.length} student(s) selected` 
					: "-- Select students --"}
				</span>
				<span className={`multiselect-arrow ${showStudentDropdown ? 'rotate' : ''}`}>▼</span>
			</div>
			{showStudentDropdown && (
				<div className="multiselect-options">
				{mockStudentProgress.map(student => (
					<div 
					key={student.id} 
					className={`multiselect-option ${newAssignment.selectedStudents.includes(student.name) ? 'selected' : ''}`}
					onClick={() => {
						const isSelected = newAssignment.selectedStudents.includes(student.name);
						let updatedStudents;
						if (isSelected) {
						updatedStudents = newAssignment.selectedStudents.filter(s => s !== student.name);
						} else {
						updatedStudents = [...newAssignment.selectedStudents, student.name];
						}
						setNewAssignment({...newAssignment, selectedStudents: updatedStudents});
					}}
					>
					<span style={{flex: 1, textAlign: 'left'}}>{student.name}</span>
					<input 
						type="checkbox" 
						checked={newAssignment.selectedStudents.includes(student.name)} 
						readOnly
					/>
					</div>
				))}
				</div>
			)}
			</div>
			<p style={{fontSize: '12px', color: '#666', marginTop: '5px'}}>Click to select/deselect students</p>
		</div>
		
		<button 
			onClick={handleCreateAssignment}
			className="create-assignment-button"
		>
			Create Assignment
		</button>
		</div>
	)}
	
	{activeAssignmentSection === 'current' && (
		<div className="current-assignments">
		<h4>Current Assignments</h4>
		<div className="assignments-list">
			{mockAssignments.map(assignment => (
			<div key={assignment.id} className="assignment-card">
				<div className="assignment-info">
				<h5>{assignment.title}</h5>
				<p className="assignment-description">{assignment.description}</p>
				<div className="assignment-meta">
					<span className="due-date">Due: {assignment.dueDate}</span>
					<span className="status">Status: {assignment.status}</span>
				</div>
				</div>
				<div className="assignment-students">
				<p><strong>Assigned to:</strong> {assignment.assignedStudents.join(', ')}</p>
				</div>
				<div className="assignment-actions">
				<button className="view-button">View Details</button>
				<button className="edit-button">Edit</button>
				<button className="delete-button">Delete</button>
				</div>
			</div>
			))}
		</div>
		</div>
	)}
	</div>
);

const renderContent = () => {
	if (activeSection === 'overview') return renderOverviewSection();
	if (activeSection === 'materials') return renderMaterialsSection();
	if (activeSection === 'video-generation') return renderMaterialGenerationSection();
	if (activeSection === 'content-generator') return renderContentGeneratorSection();
	if (activeSection === 'student-analytics') return renderStudentsSection();
	if (activeSection === 'assignments') return renderAssignmentsSection();
	if (activeSection === 'add-subject') return renderSubjectCreationSection();
	if (activeSection === 'add-user') return <AddUser activeSection={activeSection} />;
	return renderOverviewSection();
};

return (
	<div className="admin-dashboard">
	<header className="dashboard-header">
		<div className="header-left">
		<h2>Admin Dashboard</h2>
		<div className="admin-welcome">
			Welcome, {adminData.firstName} {adminData.lastName}! You have successfully logged in.
		</div>
		</div>
		<div className="header-right">
		<button onClick={handleLogout} className="logout-button">
			Logout
		</button>
		</div>
	</header>
	
	<div className="dashboard-content">
		<nav className="dashboard-sidebar">
		<ul className="sidebar-menu">
			<li 
			className={activeSection === 'overview' ? 'active' : ''}
			onClick={() => setActiveSection('overview')}
			>
			<span>Overview</span>
			</li>
			<li 
			className={activeSection === 'materials' ? 'active' : ''}
			onClick={() => setActiveSection('materials')}
			>
			<span>Materials</span>
			</li>
			<li 
			className={activeSection === 'video-generation' ? 'active' : ''}
			onClick={() => setActiveSection('video-generation')}
			>
			<span>Material Generation</span>
			</li>
			<li 
			className={activeSection === 'content-generator' ? 'active' : ''}
			onClick={() => setActiveSection('content-generator')}
			>
			<span>Content Generator</span>
			</li>
			<li 
			className={activeSection === 'student-analytics' ? 'active' : ''}
			onClick={() => setActiveSection('student-analytics')}
			>
			<span>Student Analytics</span>
			</li>
			<li 
			className={activeSection === 'assignments' ? 'active' : ''}
			onClick={() => setActiveSection('assignments')}
			>
			<span>Assignments</span>
			</li>
			<li 
			className={activeSection === 'add-subject' ? 'active' : ''}
			onClick={() => setActiveSection('add-subject')}
			>
			<span>Add Subject</span>
			</li>
			<li 
			className={activeSection === 'add-user' ? 'active' : ''}
			onClick={() => setActiveSection('add-user')}
			>
			<span>Add User</span>
			</li>
		</ul>
		</nav>
		
		<main className="dashboard-main">
		{renderContent()}
		</main>
	</div>
	</div>
);
}

export default AdminDashboard;