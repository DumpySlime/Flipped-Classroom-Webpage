import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import MaterialList from './MaterialList';
import SubjectList from './SubjectList';

function MaterialViewer(props) {
    const [selectedSubject, setSelectedSubject] = useState(null);
    const [userSubjects, setUserSubjects] = useState([]);

    const getUserInfo = () => {
        try {
            return props.userInfo || {
                id: sessionStorage.getItem('user_id'),
                username: sessionStorage.getItem('user_username'),
                firstname: sessionStorage.getItem('user_firstname'),
                lastname: sessionStorage.getItem('user_lastname'),
                role: sessionStorage.getItem('user_role'),
            };
        } catch {
            return props.userInfo || {};
        }
    };

    const userInfo = getUserInfo();

    useEffect(() => {
        const subjects = Array.isArray(props.subjects) ? props.subjects : [];
        setUserSubjects(subjects);
        console.log('MaterialViewer subjects:', subjects);
        setSelectedSubject(prev => {
            if (!prev && subjects.length > 0) {
                if (props.onSubjectChange) {
                    props.onSubjectChange(subjects[0].id);
                }
                return subjects[0];
            }
            return prev;
        });
    }, [props.subjects]); 

    const handleSubjectSelect = (subject) => {
        setSelectedSubject(subject);
        if (props.onSubjectChange) {
            props.onSubjectChange(subject.id);
        }
    };

    const getMaterialsForSubject = (subjectId) => {
        const materials = Array.isArray(props.materials) ? props.materials : [];
        return materials.filter(m => String(m.subject_id) === String(subjectId));
    };

    if (userSubjects.length === 0) {
        return (
            <div className="empty-state">
                <h3>No Subjects Assigned</h3>
                <p>You don't have any subjects assigned yet. Please contact your administrator.</p>
            </div>
        );
    }

    if (userSubjects.length === 1) {
        return (
            <MaterialList
                subject={userSubjects[0]}
                materials={getMaterialsForSubject(userSubjects[0].id)}
                userRole={props.userRole}
                userInfo={userInfo}
                onMaterialDeleted={props.onMaterialDeleted}
            />
        );
    }

    return (
        <SubjectList
            subjects={userSubjects}
            materials={props.materials}
            userRole={props.userRole}
            userInfo={userInfo}
            onSubjectSelect={handleSubjectSelect}
            onMaterialDeleted={props.onMaterialDeleted}
        />
    );
}

export default MaterialViewer;