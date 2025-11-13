import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import MaterialList from './MaterialList';
import SubjectList from './SubjectList';

function MaterialViewer(props) {
    const [userMaterials, setUserMaterials] = useState([]);
    const [userSubjects, setUserSubjects] = useState([]);

    useEffect(() => {
        if (props.activeSection !== 'materials') return;
        
        const ac = new AbortController();
        
        let subjectParams = {};
        let materialParams = {};

        // set parameters for different roles
        if (props.userRole === 'teacher') {
            subjectParams = { teacher_id: props.userInfo.id };
            materialParams = { uploaded_by: props.userInfo.id };
        } else if (props.userRole === 'student') {
            subjectParams = { student_id: props.userInfo.id };
        }

        // fetch subjects
        axios.get('/db/subject', {
            params: subjectParams, 
            signal: ac.signal
        })
        .then((response) => {
            const subjects = response.data.subjects
            setUserSubjects(subjects);
            // fetch materials and divide them by subjects
            Promise.all(subjects.map(s => {
                console.log(`Fetching materials for subject: ${s.id} (${s.subject})`);
                return axios.get('/db/material', {
                    params: {
                        ...materialParams,
                        subject_id: s.id
                    }, 
                    signal: ac.signal
                })
                .then((materialResponse) => ({
                    subjectId: s.id,
                    materials: materialResponse.data.materials
                }))
            }))
            .then(results => {
                const materialsObj = results.reduce((acc, cur) => 
                    {
                        acc[cur.subjectId] = cur.materials;
                        return acc;
                    }, {});
                setUserMaterials(materialsObj);
            })
            .catch(error => {
                if (error.name !== 'CanceledError') {
                    console.error('Error fetching materials:', error);
                }
            })
        })
        .catch((error) => {
            if (error.name !== 'CanceledError') {
                console.error('Error fetching subjects:', error);
            }
        });

        return () => ac.abort();
    }, [props.activeSection, props.userRole]);

    return (
        <>
        {userSubjects.length > 1 ? (
            <SubjectList {...props} subjects={userSubjects} materials={userMaterials} />
        ) : (
            <MaterialList {...props} subject={userSubjects} materials={userMaterials} />
        )}
        </>
    )
}

export default MaterialViewer;