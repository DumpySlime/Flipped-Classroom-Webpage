import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import MaterialList from './MaterialList';
import SubjectList from './SubjectList';

function MaterialViewer(props) {
    const [selectedSubject, setSelectedSubject] = useState(null);
    const [userMaterials, setUserMaterials] = useState({});
    const [userSubjects, setUserSubjects] = useState([]);

    // Use props data instead of fetching again
    useEffect(() => {
        // Get subjects from props
        const subjects = Array.isArray(props.subjects) ? props.subjects : [];
        setUserSubjects(subjects);
        
        console.log('MaterialViewer userSubjects:', subjects);
        
        // Get materials from props
        const materials = Array.isArray(props.materials) ? props.materials : [];
        
        // Organize materials by subject ID
        if (props.selectedSubject && materials.length > 0) {
            setUserMaterials({
                [props.selectedSubject]: materials
            });
        }
        
        // Set first subject as selected if none selected
        if (!selectedSubject && subjects.length > 0) {
            setSelectedSubject(subjects[0]);
            if (props.onSubjectChange) {
                props.onSubjectChange(subjects[0].id);
            }
        }
        
        console.log('MaterialViewer userMaterials:', materials);
    }, [props.subjects, props.materials, props.selectedSubject]);

    const handleSubjectSelect = (subject) => {
        setSelectedSubject(subject);
        if (props.onSubjectChange) {
            props.onSubjectChange(subject.id);
        }
    };

    // Get user info from localStorage if not in props
    const userInfo = props.userInfo || {
        id: localStorage.getItem('user_id'),
        username: localStorage.getItem('user_username'),
        firstname: localStorage.getItem('user_firstname'),
        lastname: localStorage.getItem('user_lastname')
    };

    return (
        <>
            {userSubjects.length === 0 ? (
                <div className="empty-state">
                    <h3>No Subjects Assigned</h3>
                    <p>You don't have any subjects assigned yet. Please contact your administrator.</p>
                </div>
            ) : userSubjects.length === 1 ? (
                // If only one subject, show MaterialList directly
                <MaterialList
                    subject={userSubjects[0]}
                    materials={userMaterials[userSubjects[0].id] || []}
                    userRole={props.userRole}
                    userInfo={userInfo}
                />
            ) : (
                // If multiple subjects, show SubjectList
                <SubjectList
                    subjects={userSubjects}
                    materials={userMaterials}
                    userRole={props.userRole}
                    userInfo={userInfo}
                    onSubjectSelect={handleSubjectSelect}
                />
            )}
        </>
    );
}

export default MaterialViewer;
