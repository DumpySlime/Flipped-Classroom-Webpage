import { useState, useEffect } from 'react';
import '../styles.css';
import '../dashboard.css';
import Overview from './sub-component/Overview';
import AddUser from './sub-component/AddUser';
import MaterialViewer from './sub-component/material-viewer/MaterialViewer';
import AddSubject from './sub-component/AddSubject';
import StudentAnalytics from './sub-component/StudentAnalytics';
import Assignment from './sub-component/Assignment';
import AIChatroom from './sub-component/chatroom/AIChatroom';

// Import API services
import { 
  materialAPI, 
  subjectAPI, 
  questionAPI, 
  studentAnswerAPI, 
  userAPI 
} from '../services/api';
import SubjectMembers from './sub-component/SubjectMembers';

function Dashboard(props) {
  const [activeSection, setActiveSection] = useState('overview');
  const [roleSections, setRoleSections] = useState({});
  const [currentUserInfo, setCurrentUserInfo] = useState({});
  
  // Real data states
  const [materials, setMaterials] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [students, setStudents] = useState([]);
  const [studentProgress, setStudentProgress] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);

  // Load initial dashboard data
  useEffect(() => {
    loadDashboardData();
  }, [props.userId, props.userRole]);

  // Define role-based sections
  useEffect(() => {
    const sections = {
      teacher: ['overview', 'materials', 'assignments', 'analytics', 'subjects', 'users', 'chatroom'],
      student: ['overview', 'materials', 'assignments', 'analytics', 'chatroom'],
      admin: ['overview', 'materials', 'assignments', 'analytics', 'subjects', 'users', 'chatroom']
    };
    setRoleSections(sections[currentUserInfo.role] || sections.student);
  }, [currentUserInfo.role]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get user info
      const userId = props.userId || localStorage.getItem('user_id');
      const userRole = props.userRole || localStorage.getItem('user_role');
      
      if (!userId || !userRole) {
        throw new Error('User information not available');
      }
      
      setCurrentUserInfo({ id: userId, role: userRole });
      
      // Fetch subjects
      const subjectsData = await subjectAPI.getAll(userId, userRole);
      setSubjects(subjectsData);
      
      // Set first subject as selected and fetch its materials
      if (subjectsData.length > 0) {
        setSelectedSubject(subjectsData[0].id);
        const materialsData = await materialAPI.getAll(subjectsData[0].id);
        setMaterials(materialsData);
      }
      
      // Teacher-specific data
      if (userRole === 'teacher') {
        const studentsData = await userAPI.getAll('student');
        setStudents(studentsData);
        
        // Calculate student progress
        const progressData = await Promise.all(
          studentsData.map(async (student) => {
            const answers = await studentAnswerAPI.getAll(student.id);
            return {
              id: student.id,
              name: student.username,
              progress: calculateProgress(answers),
              lastActivity: getLastActivity(answers)
            };
          })
        );
        setStudentProgress(progressData);
      }
      
      // Student-specific data
      if (userRole === 'student') {
        const assignmentsData = [];
        for (const subject of subjectsData) {
          const subjectMaterials = await materialAPI.getAll(subject.id);
          assignmentsData.push(...subjectMaterials);
        }
        setAssignments(assignmentsData);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  const calculateProgress = (answers) => {
    if (!answers || answers.length === 0) return 0;
    const totalScore = answers.reduce((sum, submission) => sum + (submission.total_score || 0), 0);
    const maxScore = answers.length * 100;
    return Math.round((totalScore / maxScore) * 100);
  };

  const getLastActivity = (answers) => {
    if (!answers || answers.length === 0) return 'No activity';
    const latest = answers.reduce((latest, submission) => {
      const submissionDate = new Date(submission.submission_time);
      return submissionDate > new Date(latest) ? submission.submission_time : latest;
    }, answers[0].submission_time);
    return new Date(latest).toLocaleString();
  };

  const handleSubjectChange = async (subjectId) => {
    setSelectedSubject(subjectId);
    setLoading(true);
    try {
      const materialsData = await materialAPI.getAll(subjectId);
      setMaterials(materialsData);
    } catch (error) {
      console.error('Error fetching materials:', error);
    }
    setLoading(false);
  };

  const handleAddMaterial = async (materialData) => {
    const newMaterial = await materialAPI.add({
      ...materialData,
      subject_id: selectedSubject,
      user_id: currentUserInfo.id
    });
    
    // Refresh materials
    const materialsData = await materialAPI.getAll(selectedSubject);
    setMaterials(materialsData);
    
    return newMaterial;
  };

  const handleDeleteMaterial = async (materialId) => {
    await materialAPI.delete(materialId);
    
    // Refresh materials
    const materialsData = await materialAPI.getAll(selectedSubject);
    setMaterials(materialsData);
  };

  const handleSubmitAnswers = async (answersData) => {
    const result = await studentAnswerAPI.submit({
      ...answersData,
      student_id: currentUserInfo.id
    });
    
    // Refresh assignments
    const assignmentsData = [];
    for (const subject of subjects) {
      const subjectMaterials = await materialAPI.getAll(subject.id);
      assignmentsData.push(...subjectMaterials);
    }
    setAssignments(assignmentsData);
    
    return result;
  };

  const handleAddQuestion = async (questionData) => {
    return await questionAPI.add({
      ...questionData,
      user_id: currentUserInfo.id
    });
  };

  const handleLogout = () => {
    // Clear all localStorage data
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_firstname');
    localStorage.removeItem('user_lastname');
    localStorage.removeItem('user_username');
    localStorage.removeItem('user');
    
    // Redirect to login
    window.location.href = '/';
  };

  if (loading && !materials.length) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <p>Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (error && !materials.length) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-error">
          <h2>Error Loading Dashboard</h2>
          <p>{error}</p>
          <button onClick={() => loadDashboardData()}>Retry</button>
        </div>
      </div>
    );
  }

  const totalStudents = students.length;

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'overview':
        return (
          <Overview
            materials={materials}
            subjects={subjects}
            students={students}
            studentProgress={studentProgress}
            totalStudents={totalStudents}
            userRole={currentUserInfo.role}
          />
        );
  // Load initial dashboard data
		case 'materials':
		return (
			<MaterialViewer
			subjects={subjects}
			materials={materials}
			selectedSubject={selectedSubject}
			onSubjectChange={handleSubjectChange}
			userRole={currentUserInfo.role}
			userInfo={{
				id: currentUserInfo.id,
				username: localStorage.getItem('user_username'),
				firstname: localStorage.getItem('user_firstname'),
				lastname: localStorage.getItem('user_lastname')
			}}
			activeSection={activeSection}
			/>
		);

      case 'assignments':
        return (
          <Assignment
            assignments={assignments}
            materials={materials}
            onSubmitAnswers={handleSubmitAnswers}
            fetchQuestions={questionAPI.getByMaterial}
            userRole={currentUserInfo.role}
            userId={currentUserInfo.id}
          />
        );
      case 'analytics':
        return (
          <StudentAnalytics
            studentId={currentUserInfo.id}
            studentProgress={studentProgress}
            students={students}
            fetchStudentAnswers={studentAnswerAPI.getAll}
            userRole={currentUserInfo.role}
          />
        );
      case 'subjects':
        return (
          <AddSubject
            subjects={subjects}
            onSubjectsUpdate={async () => {
              const subjectsData = await subjectAPI.getAll(currentUserInfo.id, currentUserInfo.role);
              setSubjects(subjectsData);
            }}
          />
        );
      case 'users':
        return (
          <AddUser
            onUsersUpdate={async () => {
              const studentsData = await userAPI.getAll('student');
              setStudents(studentsData);
            }}
          />
        );
      case 'chatroom':
        return (
          <AIChatroom
            userId={currentUserInfo.id}
            materials={materials}
          />
        );
      default:
        return (
          <Overview
            materials={materials}
            subjects={subjects}
            students={students}
            studentProgress={studentProgress}
            totalStudents={totalStudents}
            userRole={currentUserInfo.role}
          />
        );
    }
  };
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
    //assignments: 'Assignments',
    'student-analytics': 'Student Analytics',
	chatroom: 'AI Chatroom'
  },
  teacher: {
    overview: 'Overview',
    materials: 'Materials',
    //assignments: 'Assignments',
    'student-analytics': 'Student Analytics',
	'subject-members': 'Subject Members',
	chatroom: 'AI Chatroom'
  },
  admin: {
    overview: 'Overview',
    materials: 'Materials',
    //assignments: 'Assignments',
    'student-analytics': 'Student Analytics',
    'add-subject': 'Add Subject',
    'add-user': 'Add User',
	'subject-members': 'Subject Members',
	chatroom: 'AI Chatroom'
  }
};

const renderContent = () => {
	if (activeSection === 'overview') return <Overview activeSection={activeSection} totalStudents={totalStudents} mockMaterials={mockMaterials} mockGeneratedContent={mockGeneratedContent} mockGeneratedVideos={mockGeneratedVideos}/>;
	if (activeSection === 'materials') return <MaterialViewer activeSection={activeSection} userInfo={props.userInfo} userRole={props.userRole} mockMaterials={mockMaterials}/>;
	if (activeSection === 'student-analytics') return <StudentAnalytics activeSection={activeSection} mockStudentProgress={mockStudentProgress}/>;
	//if (activeSection === 'assignments') return <Assignment activeSection={activeSection} mockAssignments={mockAssignments} mockStudentProgress={mockStudentProgress}/>;
	if (activeSection === 'add-subject') return <AddSubject activeSection={activeSection} />;
	if (activeSection === 'add-user') return <AddUser setActiveSection={setActiveSection} />;
	if (activeSection === 'subject-members') return <SubjectMembers userInfo={props.userInfo} userRole={props.userRole} />;
	if (activeSection === 'chatroom') return <AIChatroom />;
	return <Overview activeSection={activeSection} totalStudents={totalStudents} mockMaterials={mockMaterials} mockGeneratedContent={mockGeneratedContent} mockGeneratedVideos={mockGeneratedVideos}/>;
};
	
useEffect(() => {
	setRoleSections(allowedSectionsByRole[props.userRole]);
	setCurrentUserInfo(props.userInfo);
}, [props.userRole]);

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Dashboard</h2>
          <div className="user-info">
            <div className="user-details">
              <span className="user-name">
                {localStorage.getItem('user_firstname')} {localStorage.getItem('user_lastname')}
              </span>
              <span className="user-role">
                {currentUserInfo.role || localStorage.getItem('user_role')}
              </span>
            </div>
            <button 
              className="logout-button"
              onClick={handleLogout}
            >
              🚪 Logout
            </button>
          </div>
        </div>
        <nav className="sidebar-nav">
          {roleSections.includes && roleSections.includes('overview') && (
            <button
              className={activeSection === 'overview' ? 'active' : ''}
              onClick={() => {setActiveSection('overview'); 
				loadDashboardData();}}
            >
              📊 Overview
            </button>
          )}
          {roleSections.includes && roleSections.includes('materials') && (
            <button
              className={activeSection === 'materials' ? 'active' : ''}
              onClick={() => setActiveSection('materials')}
            >
              📚 Materials
            </button>
          )}
          {roleSections.includes && roleSections.includes('assignments') && (
            <button
              className={activeSection === 'assignments' ? 'active' : ''}
              onClick={() => setActiveSection('assignments')}
            >
              📝 Assignments
            </button>
          )}
          {roleSections.includes && roleSections.includes('analytics') && (
            <button
              className={activeSection === 'analytics' ? 'active' : ''}
              onClick={() => setActiveSection('analytics')}
            >
              📈 Analytics
            </button>
          )}
          {roleSections.includes && roleSections.includes('subjects') && (
            <button
              className={activeSection === 'subjects' ? 'active' : ''}
              onClick={() => setActiveSection('subjects')}
            >
              📖 Subjects
            </button>
          )}
          {roleSections.includes && roleSections.includes('users') && (
            <button
              className={activeSection === 'users' ? 'active' : ''}
              onClick={() => setActiveSection('users')}
            >
              👥 Users
            </button>
          )}
          {roleSections.includes && roleSections.includes('chatroom') && (
            <button
              className={activeSection === 'chatroom' ? 'active' : ''}
              onClick={() => setActiveSection('chatroom')}
            >
              💬 AI Chatroom
            </button>
          )}
        </nav>
      </aside>
      <main className="main-content">
        {renderActiveSection()}
      </main>
    </div>
  );
}

export default Dashboard;
