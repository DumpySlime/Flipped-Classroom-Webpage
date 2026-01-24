import { useState, useEffect } from 'react';
import '../../styles.css';
import '../../dashboard.css';
import MaterialList from './material-viewer/MaterialList';

function Overview(props) {
  // Destructure props with default values
  const {
    materials = [],
    subjects = [],
    students = [],
    studentProgress = [],
    totalStudents = 0,
    userRole = 'student',
    activeSection
  } = props;

  // Safe arrays in case props are undefined
  const safeMaterials = Array.isArray(materials) ? materials : [];
  const safeSubjects = Array.isArray(subjects) ? subjects : [];
  const safeStudents = Array.isArray(students) ? students : [];
  const safeProgress = Array.isArray(studentProgress) ? studentProgress : [];

  // Sort materials by created_at in descending order (newest first)
  const sortedMaterials = [...safeMaterials].sort((a, b) => {
    const dateA = new Date(a.created_at || 0);
    const dateB = new Date(b.created_at || 0);
    return dateB - dateA; // Descending order (newest first)
  });

  useEffect(() => {
    if (activeSection !== 'overview') return;
    // Fetch data if needed
  }, [activeSection]);

  const [selectedSubject, setSelectedSubject] = useState(null);
  const userInfo = props.userInfo;

  // Direct user to selected subject Material List on click
  function handleViewMaterialList(subject) {
    setSelectedSubject(subject);
  }

  if (selectedSubject) {
    const subjectMaterials = safeMaterials.filter(m => m.subject_id === selectedSubject.id) || [];
    return (
      <MaterialList
        subject={selectedSubject}
        materials={subjectMaterials}
        userRole={userRole}
        userInfo={userInfo}
        onClose={() => setSelectedSubject(null)}
      />
    );
  }

  return (
    <div className="dashboard-main">
      <h2>Dashboard Overview</h2>
      
      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Students</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '10px 0' }}>
            {totalStudents || safeStudents.length}
          </p>
        </div>

        <div className="stat-card">
          <h3>Total Materials</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '10px 0' }}>
            {safeMaterials.length}
          </p>
        </div>

        <div className="stat-card">
          <h3>Total Subjects</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '10px 0' }}>
            {safeSubjects.length}
          </p>
        </div>
      </div>

      {/* Recent Materials - Using sorted materials */}
      {sortedMaterials.length > 0 && (
        <div className="recent-activity">
          <h4>Recent Materials</h4>
          <div className="activity-list">
            {sortedMaterials.slice(0, 5).map((material) => (
              <div key={material.id} className="activity-item">
                <span>
                  <strong>{material.topic}</strong>
                  {material.subject && (
                    <span style={{ 
                      marginLeft: '8px', 
                      fontSize: '12px', 
                      color: '#666',
                      background: '#e0e0e0',
                      padding: '2px 8px',
                      borderRadius: '4px'
                    }}>
                      {material.subject}
                    </span>
                  )}
                </span>
                <span className="activity-time">
                  {material.created_at 
                    ? new Date(material.created_at).toLocaleString() 
                    : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Student Progress (Teacher only) */}
      {userRole === 'teacher' && safeProgress.length > 0 && (
        <div className="recent-activity">
          <h4>Student Progress</h4>
          <div className="activity-list">
            {safeProgress.slice(0, 5).map((student) => (
              <div key={student.id} className="activity-item">
                <span>{student.name}</span>
                <span style={{ 
                  fontWeight: 'bold', 
                  color: student.progress >= 70 ? '#27ae60' : '#e74c3c' 
                }}>
                  {student.progress}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Subjects List */}
      {safeSubjects.length > 0 && (
        <div className="recent-activity">
          <h4>Your Subjects</h4>
          <div className="courses-list">
            {safeSubjects.map((subject) => (
              <div key={subject.id} className="course-card" onClick={() => handleViewMaterialList(subject)}>
                <h3>{subject.subject}</h3>
                <p>{subject.topics?.length || 0} topics</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {safeMaterials.length === 0 && safeSubjects.length === 0 && (
        <div className="activity-list" style={{ textAlign: 'center', padding: '40px' }}>
          <h3>📭 No Data Available</h3>
          <p>Start by adding subjects and materials to get started!</p>
        </div>
      )}
    </div>
  );
}

export default Overview;
