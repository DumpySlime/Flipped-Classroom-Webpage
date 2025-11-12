import { useState, useEffect } from 'react';
import '../../../styles.css';
import '../../../dashboard.css';
import axios from 'axios';
import MaterialList from './MaterialList';
import SubjectList from './SubjectList';

function MaterialViewer(props) {
    const [userMaterials, setUserMaterials] = useState([]);
    const [userSubjects, setUserSubjects] = useState([]);
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
        
        let subjectParams = {};
        let materialParams = {};

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
            Promise.all(subjects.map(s =>
                axios.get('/db/material', {
                    params: {
                        ...materialParams,
                        subject_ids: s.id
                    }, 
                    signal: ac.signal
                })
                .then((materialResponse) => ({
                    subjectId: s.id,
                    materials: materialResponse.data.materials
                }))
            ))
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
        {Object.keys(userSubjects).length > 1 ? (
            <SubjectList {...props} subjects={userSubjects} materials={userMaterials} />
        ) : (
            <MaterialList {...props} subject={userSubjects} materials={userMaterials} />
        )}
        </>
    )
}

export default MaterialViewer;