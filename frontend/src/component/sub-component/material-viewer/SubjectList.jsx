import { useState } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import MaterialList from './MaterialList';

function SubjectList({ subjects, materials, userRole, userInfo, activeSection, ...props }) {
  const [selectedSubject, setSelectedSubject] = useState(null);

  // Early return for loading state
  if (!subjects || subjects.length === 0) {
    return (
      <div className="subject-section">
        <div className="section-header">
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading subjects...</p>
          </div>
        </div>
      </div>
    );
  }

  // Selected subject view
  if (selectedSubject) {
    return (
      <div className="subject-detail-view">
        <MaterialList 
          {...props}
          subject={selectedSubject}
          materials={materials?.[selectedSubject.id] || []}
          userRole={userRole}
          userInfo={userInfo}
          activeSection={activeSection}
          subjectLength={subjects.length}
          onBackToSubjectList={() => setSelectedSubject(null)}
        />
      </div>
    );
  }

  // Subjects list view
  return (
    <div className="subject-section">
      <div className="section-header">
        <div className="header-content">
          <h3 className="section-title">📚 Subjects</h3>
          <div className="subject-stats">
            <span className="stat-badge">{subjects.length} subjects</span>
          </div>
        </div>
      </div>

      {/* Subject Grid */}
      <div className="subject-grid">
        {subjects.map((subject) => (
          <SubjectCard
            key={subject.id}
            subject={subject}
            onClick={() => setSelectedSubject(subject)}
            materialsCount={materials?.[subject.id]?.length || 0}
          />
        ))}
      </div>

      {/* Empty state fallback */}
      {subjects.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📂</div>
          <h4>No subjects available</h4>
          <p>Contact your teacher to get started.</p>
        </div>
      )}
    </div>
  );
}

function SubjectCard({ subject, onClick, materialsCount }) {
  return (
    <div 
      className="subject-card"
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`View ${subject.subject} materials`}
    >
      <div className="card-gradient">
        <div className="card-header">
          <div className="subject-icon">📖</div>
          <div className="subject-count">
            {materialsCount > 0 ? (
              <span className="count-badge">{materialsCount}</span>
            ) : (
              <span className="count-empty">Empty</span>
            )}
          </div>
        </div>
        <div className="card-content">
          <h4 className="subject-title">{subject.subject}</h4>
          {subject.topics?.length > 0 && (
            <div className="topics-preview">
              <span className="topic-tag">{subject.topics[0]}</span>
              {subject.topics.length > 1 && (
                <span className="more-topics">+{subject.topics.length - 1}</span>
              )}
            </div>
          )}
        </div>
        <div className="card-footer">
          <div className="action-prompt">
            <span>Click to view materials</span>
            <span className="arrow-right">→</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SubjectList;
