import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import MaterialList from './MaterialList';
import SubjectList from './SubjectList';

function MaterialViewer(props) {
    const [userMaterials, setUserMaterials] = useState({});
    const [userSubjects, setUserSubjects] = useState({});
    /*
        if teacher => 
            fetch subjects with teacher id
            fetch materials with subject ids and teacher id
            if multiple subjects => show subject list view
            else => show material list view

        if student => fetch subjects enrolled by student
            fetch subjects with teacher id
            fetch materials with subject ids and teacher id
            if multiple subjects => show subject list view
            else => show material list view

        if admin => if multiple subjects => show subject list view
            else => show material list view
    */

    useEffect(() => {
        if (props.activeSection !== 'materials') return;
        
        const ac = new AbortController();
        switch (props.userRole) {
            case 'teacher':
                // fetch subjects taught by teacher
                axios.get('/db/subject', {
                    params: {
                        teacher_id: props.userInfo.id
                    }
                })
                .then((response) => {
                    setUserSubjects(response.subject);
                    // fetch materials for subjects taught by that teacher
                    response.subjects.map(s => {
                        axios.get('/db/material', {
                            params: {
                                uploaded_by: props.userInfo.id,
                                subject_ids: s.id
                            }
                        })
                        .then((response) => {
                            setUserMaterials(prevMaterials => ({
                                ...prevMaterials,
                                [s.id]: response.materials
                            }));
                        })
                        .catch((error) => {
                            console.error('Error fetching materials for teacher:', error);
                        });
                    });
                })
                .catch((error) => {
                    console.error('Error fetching subjects for teacher:', error);
                });
                break;
            case 'student':
                // fetch subjects taught by teacher
                axios.get('/db/subject', {
                    params: {
                        student_id: props.userInfo.id
                    }
                })
                .then((response) => {
                    setUserSubjects(response.subject);
                    // fetch materials for subjects the student enrolled
                    response.subjects.map(s => {
                        axios.get('/db/material', {
                            params: {
                                subject_ids: s.id
                            }
                        })
                        .then((response) => {
                            setUserMaterials(prevMaterials => ({
                                ...prevMaterials,
                                [s.id]: response.materials
                            }));
                        })
                        .catch((error) => {
                            console.error('Error fetching materials for student:', error);
                        });
                    });
                })
                .catch((error) => {
                    console.error('Error fetching subjects for student:', error);
                });
                break;
            case 'admin':
                // fetch subjects
                axios.get('/db/subject')
                .then((response) => {
                    setUserSubjects(response.subject);
                    response.subjects.map(s => {
                        axios.get('/db/material')
                        .then((response) => {
                            setUserMaterials(prevMaterials => ({
                                ...prevMaterials,
                                [s.id]: response.materials
                            }));
                        })
                        .catch((error) => {
                            console.error('Error fetching materials for admin:', error);
                        });
                    });
                })
                .catch((error) => {
                    console.error('Error fetching subjects for admin:', error);
                });
                break;
        };
        return () => ac.abort();
    }, [props.activeSection, props.userRole]);
    
    return (
        <>
        {Object.keys(userSubjects).length > 1 ? (
            <SubjectList {...props} subjects={userSubjects} materials={userMaterials} />
        ) : (
            <MaterialList {...props} subject={userSubjects} materials={userMaterials} />
        )}
        </>
    )
}

export default MaterialViewer;