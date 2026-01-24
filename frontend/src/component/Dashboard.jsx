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
import SubjectMembers from './sub-component/SubjectMembers';

// Import API services
import { 
  materialAPI, 
  subjectAPI, 
  questionAPI, 
  studentAnswerAPI, 
  userAPI 
} from '../services/api';

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
      teacher: ['overview', 'materials', 'analytics', 'subject-members'],
      student: ['overview', 'materials', 'chatroom'],
      admin: ['overview', 'materials', 'analytics', 'subjects', 'users', 'chatroom', 'subject-members']
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
      case 'subject-members':
        return (
          <SubjectMembers
            userInfo={{
              id: currentUserInfo.id,
              username: localStorage.getItem('user_username'),
              firstname: localStorage.getItem('user_firstname'),
              lastname: localStorage.getItem('user_lastname')
            }}
            userRole={currentUserInfo.role}
            subjects={subjects}
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
          {roleSections.includes && roleSections.includes('subject-members') && (
            <button
              className={activeSection === 'subject-members' ? 'active' : ''}
              onClick={() => setActiveSection('subject-members')}
            >
              🧑‍🤝‍🧑 Subject Members
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
