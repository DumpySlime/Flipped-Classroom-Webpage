import '../../../styles.css';
import '../../../dashboard.css';

import MaterialList from './MaterialList';

function SubjectList(props) {

    const handleSubjectSelect = (subject) => {
        return (
            <MaterialList {...props} subject={subject}/>
        );
    }

    return (
        <div className="materials-section">
        <div className="section-header">
            <h3>Subjects</h3>
        </div>
        {/* Subject List */}
        <div className="materials-list">
            {props.userSubjects.map(s => (
            <div key={s.id} className="material-card" onClick={() => handleSubjectSelect(s)}>
                <div className="material-info">
                <h4>{s.subject}</h4>
                </div>
            </div>
            ))}
        </div>
        </div>
    )
}

export default SubjectList;