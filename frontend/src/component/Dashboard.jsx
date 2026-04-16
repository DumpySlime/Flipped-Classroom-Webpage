import { useState, useEffect, useRef, useCallback } from 'react';
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
import { useTranslation } from 'react-i18next';

import { 
  materialAPI, 
  subjectAPI, 
  questionAPI, 
  studentAnswerAPI, 
  userAPI 
} from '../services/api';

function Dashboard(props) {
  const [activeSection, setActiveSection] = useState('overview');
  const [roleSections, setRoleSections] = useState([]);
  const [currentUserInfo, setCurrentUserInfo] = useState({});
  
  const [materials, setMaterials] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [students, setStudents] = useState([]);
  const [studentProgress, setStudentProgress] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const { t, i18n } = useTranslation();
  const [currentLang, setCurrentLang] = useState(
    localStorage.getItem('lang') || i18n.language
  );
  const isMountedRef = useRef(true);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const userId = props.userId || sessionStorage.getItem('user_id');
      const userRole = props.userRole || sessionStorage.getItem('user_role');

      if (!userId || !userRole) {
        throw new Error('User information not available');
      }

      if (!isMountedRef.current) return;
      setCurrentUserInfo({ id: userId, role: userRole });

      const subjectsData = await subjectAPI.getAll(userId, userRole);
      if (!isMountedRef.current) return;
      setSubjects(subjectsData);

      if (subjectsData.length > 0) {
        setSelectedSubject(subjectsData[0].id);
        const materialsData = await materialAPI.getAll(subjectsData[0].id);
        if (!isMountedRef.current) return;
        setMaterials(materialsData);
      } else {
        setSelectedSubject(null);
        setMaterials([]);
      }

      if (userRole === 'teacher' || userRole === 'admin') {
        const studentsData = await userAPI.getAll('student');
        if (!isMountedRef.current) return;
        setStudents(studentsData);

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
        if (!isMountedRef.current) return;
        setStudentProgress(progressData);
      } else {
        setStudents([]);
        setStudentProgress([]);
      }

      if (userRole === 'student') {
        const assignmentsData = [];
        for (const subject of subjectsData) {
          const subjectMaterials = await materialAPI.getAll(subject.id);
          assignmentsData.push(...subjectMaterials);
        }
        if (!isMountedRef.current) return;
        setAssignments(assignmentsData);
      } else {
        setAssignments([]);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      if (!isMountedRef.current) return;
      setError(error.message);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [props.userId, props.userRole]);

  useEffect(() => {
    isMountedRef.current = true;
    loadDashboardData();
    return () => {
      isMountedRef.current = false;
    };
  }, [loadDashboardData]);

  useEffect(() => {
    if (!currentUserInfo.role) return;
    const sections = {
      teacher: ['overview', 'materials', 'analytics'],
      student: ['overview', 'materials', 'chatroom'],
      admin: ['overview', 'materials', 'analytics', 'subjects', 'users', 'chatroom', 'subject-members']
    };
    setRoleSections(sections[currentUserInfo.role] || sections.student);
  }, [currentUserInfo.role]);

  const calculateProgress = (answers) => {
    if (!answers || answers.length === 0) return 0;
    const totalScore = answers.reduce((sum, submission) => sum + (submission.total_score || 0), 0);
    const maxScore = answers.length * 100;
    return Math.round((totalScore / maxScore) * 100);
  };

  const getLastActivity = (answers) => {
    if (!answers || answers.length === 0) return 'No activity';
    const latestTime = answers.reduce((latestTimestamp, submission) => {
      const t = new Date(submission.submission_time).getTime();
      return t > latestTimestamp ? t : latestTimestamp;
    }, 0);
    return latestTime ? new Date(latestTime).toLocaleString() : 'No activity';
  };

  const handleSubjectChange = async (subjectId) => {
    setSelectedSubject(subjectId);
    setLoading(true);
    try {
      const materialsData = await materialAPI.getAll(subjectId);
      setMaterials(materialsData);
    } catch (error) {
      console.error('Error fetching materials:', error);
    } finally {
      setLoading(false);
    }
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
    // Clear all sessionStorage data
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_id');
    sessionStorage.removeItem('user_role');
    sessionStorage.removeItem('user_firstname');
    sessionStorage.removeItem('user_lastname');
    sessionStorage.removeItem('user_username');
    sessionStorage.removeItem('user');
    
    // Redirect to login
    window.location.href = '/';
  };

  if (loading && !materials.length) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-loading">
          <div className="spinner"></div>
          <p>{t('loadingDashboard')}</p>
        </div>
      </div>
    );
  }

  if (error && !materials.length) {
    return (
      <div className="dashboard-container">
        <div className="dashboard-error">
          <h2>{t('errorLoadingDashboard')}</h2>
          <p>{error}</p>
          <button onClick={loadDashboardData}>{t('retry')}</button>
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
            userInfo={{
              id: currentUserInfo.id,
              username: sessionStorage.getItem('user_username'),
              firstname: sessionStorage.getItem('user_firstname'),
              lastname: sessionStorage.getItem('user_lastname')
            }}
          />
        );
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
              username: sessionStorage.getItem('user_username'),
              firstname: sessionStorage.getItem('user_firstname'),
              lastname: sessionStorage.getItem('user_lastname')
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
          username: sessionStorage.getItem('user_username'),
          firstname: sessionStorage.getItem('user_firstname'),
          lastname: sessionStorage.getItem('user_lastname')
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
            userInfo={{
              id: currentUserInfo.id,
              username: sessionStorage.getItem('user_username'),
              firstname: sessionStorage.getItem('user_firstname'),
              lastname: sessionStorage.getItem('user_lastname')
            }}
          />
        );
    }
  };

  return (
    <div className="dashboard-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>{t('dashboardTitle')}</h2>
          <div className="user-info">
            <div className="user-details">
              <span className="user-name">
                {sessionStorage.getItem('user_firstname')} {sessionStorage.getItem('user_lastname')}
              </span>
              <span className="user-role">
                {currentUserInfo.role || sessionStorage.getItem('user_role')}
              </span>
            </div>
            <button 
              className="logout-button"
              onClick={handleLogout}
            >
              {t('logout')}
            </button>
          </div>
        </div>
        <nav className="sidebar-nav">
          {roleSections.includes('overview') && (
            <button
              className={activeSection === 'overview' ? 'active' : ''}
              onClick={() => {setActiveSection('overview'); 
				loadDashboardData();}}
            >
              {t('navOverview')}
            </button>
          )}
          {roleSections.includes('subject-members') && (
            <button
              className={activeSection === 'subject-members' ? 'active' : ''}
              onClick={() => setActiveSection('subject-members')}
            >
              {t('navSubjectMembers')}
            </button>
          )}
          {roleSections.includes('materials') && (
            <button
              className={activeSection === 'materials' ? 'active' : ''}
              onClick={() => setActiveSection('materials')}
            >
              {t('navMaterials')}
            </button>
          )}
          {roleSections.includes('assignments') && (
            <button
              className={activeSection === 'assignments' ? 'active' : ''}
              onClick={() => setActiveSection('assignments')}
            >
              {t('navAssignments')}
            </button>
          )}
          {roleSections.includes('analytics') && (
            <button
              className={activeSection === 'analytics' ? 'active' : ''}
              onClick={() => setActiveSection('analytics')}
            >
              {t('navAnalytics')}
            </button>
          )}
          {roleSections.includes('subjects') && (
            <button
              className={activeSection === 'subjects' ? 'active' : ''}
              onClick={() => setActiveSection('subjects')}
            >
              {t('navSubjects')}
            </button>
          )}
          {roleSections.includes('users') && (
            <button
              className={activeSection === 'users' ? 'active' : ''}
              onClick={() => setActiveSection('users')}
            >
              {t('navUsers')}
            </button>
          )}
          {roleSections.includes('chatroom') && (
            <button
              className={activeSection === 'chatroom' ? 'active' : ''}
              onClick={() => setActiveSection('chatroom')}
            >
              {t('navChatroom')}
            </button>
          )}
        </nav>
        <div className="sidebar-language">
          <button 
            onClick={() => {
              i18n.changeLanguage('en');
              setCurrentLang('en');
              localStorage.setItem('lang', 'en');
            }} 
            className={`lang-btn ${currentLang === 'en' ? 'lang-active' : ''}`}
          >
            EN
          </button>
          <button 
            onClick={() => {
              i18n.changeLanguage('zh-HK');
              setCurrentLang('zh-HK');
              localStorage.setItem('lang', 'zh-HK');
            }} 
            className={`lang-btn ${currentLang === 'zh-HK' ? 'lang-active' : ''}`}
          >
            繁體中文(香港)
          </button>
        </div>
      </aside>
      <main className="main-content">
        {renderActiveSection()}
      </main>
    </div>
  );
}

export default Dashboard;
