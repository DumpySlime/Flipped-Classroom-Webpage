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
            subjectParams = { "teacher_id": props.userInfo.id };
            materialParams = { "uploaded_by": props.userInfo.id };
        } else if (props.userRole === 'student') {
            subjectParams = { "student_id": props.userInfo.id };
        }

        console.log(`/db/subject params: ${JSON.stringify(subjectParams)}`);
        console.log(`/db/material params: ${JSON.stringify(materialParams)}`);

        // fetch subjects
        axios.get('/db/subject', {
            params: subjectParams,
            signal: ac.signal
        })
        .then((response) => {
            const subjects = response.data.subjects || [];
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
                .then((response) => {
                    console.log(`Materials response for subjectId ${s.id}:`, response.data);
                    return {
                        subjectId: s.id,
                        materials: response.data.materials
                    }
                })
                .catch((error) => {
                    if (error.name != 'CanceledError') {
                        console.error('Error in Promise: ', error);
                    }
                    return { subjectId: s.id, materials: [] };
                })
            }))
            .then(results => {
                console.log("MaterialViewer material response:", JSON.stringify(results,null,2))
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

    useEffect(() => {
        console.log("MaterialViewer userSubjects: ", JSON.stringify(userSubjects, null, 2));
        console.log("MaterialViewer userMaterials: ", JSON.stringify(userMaterials, null, 2));
    }, [userSubjects, userMaterials])

    return (
        <>
        {userSubjects.length === 1 ? (
            
            <MaterialList {...props} subject={userSubjects[0]} materials={userMaterials[userSubjects[0]?.id] || [] } />
        ) : (userSubjects.length > 1 ?            
            <SubjectList {...props} subjects={userSubjects} materials={userMaterials} /> : <div>There is no subject assigned</div>    
        )}
        </>
    )
}

export default MaterialViewer;