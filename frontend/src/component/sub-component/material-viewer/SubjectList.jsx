import '../../../styles.css';
import '../../../dashboard.css';
import { useState } from 'react'

import MaterialList from './MaterialList';

function SubjectList(props) {

    const [selectedSubject, setSelectedSubject] = useState(null)

    if (selectedSubject) {
        return (
            <div>
                {
                    (props.subjects.length > 1) ? <button onClick={() => setSelectedSubject(null)}>Back to Subjects</button> : null
                }
                <MaterialList {...props} subject={selectedSubject} materials={props.materials[selectedSubject.id] || []}/>
            </div>
        );
    }

    if (!props.subjects || props.subjects.length === 0) {
        return <div>Loading subjects...</div>;
    }

    return (
        <div className="subject-section">
            <div className="section-header">
                <h3>Subjects</h3>
            </div>
            {/* Subject List */}
            <div className="subject-list">
                {props.subjects.map((s) => (
                <div key={s.id} className="course-card" onClick={() => setSelectedSubject(s)}>
                    <div className="course-info">
                    <h4>{s.subject}</h4>
                    </div>
                </div>
                ))}
            </div>
        </div>
    )
}

export default SubjectList;