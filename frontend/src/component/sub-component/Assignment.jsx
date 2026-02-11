import { useState , useEffect } from 'react';
import '../../styles.css';
import '../../dashboard.css';

function Assignment(props) {
    
	const [activeAssignmentSection, setActiveAssignmentSection] = useState('manage');

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

    useEffect(() => {
        if (props.activeSection !== 'assignments') return;
        // Fetch data if needed
    }, [props.activeSection]);

    return (
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
                    {props.mockStudentProgress.map(student => (
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
                {props.mockAssignments.map(assignment => (
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
}

export default Assignment;