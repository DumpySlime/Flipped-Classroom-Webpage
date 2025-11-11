import { useState, useEffect } from 'react';
import axios from 'axios';
import '../../styles.css';
import '../../dashboard.css';

function SubjectCreation(props) {

    const [allTeachers, setAllTeachers] = useState([]);
    const [selectedTeacherIds, setSelectedTeacherIds] = useState([]);
    const [activeTabId, setActiveTabId] = useState(null);

    const [loadingTeachers, setLoadingTeachers] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (props.activeSection !== 'add-subject') return;
        const ac = new AbortController();

        console.log('Fetching teachers for subject creation...');
        (() => {
        setLoadingTeachers(true);
        setError(null);
        axios.get('/db/user', {
            params: {
                role: "teacher"
            }
        })
        .then(function (response) {
            console.log(`response: ${response}`);
            const data = response.data;
            console.log(`Fetched teacher data: ${data}`);
            const list = (data.users || []).map(t => ({
                id: t.id,
                name: t.username
            }));
            setAllTeachers(list);
            const ids = list.map(t => t.id);
            setSelectedTeacherIds(ids);
            if (ids.length) setActiveTabId(ids[0]);
        })
        .catch(function (error) {
            console.log(error);
            if (error.name !== 'AbortError') setError('Failed to load teachers');
        })
        .finally(function () {
            setLoadingTeachers(false);
        });
        })();
        return () => ac.abort();
    }, [props.activeSection]);

    // create buttons for + - subjects
    const [topics, setTopics] = useState(['']);

    const addTopic = () => {
        setTopics(topics => [...topics, '']);
    }

    const updateTopic = (idx, value) => {
        setTopics(prev => {
        const copy = [...prev];
        copy[idx] = value;
        return copy;
        });
    };

    const removeTopic = (idx) => {
        setTopics(prev => prev.filter((_, i) => i !== idx));
    };

    // add subject button
    const handleSubmitSubject = async() => {
        const subjectName = (document.getElementById('subject-input')?.value || '').trim();
        
        if (!subjectName) {
            alert('Please enter a subject name');
            return;
        }
        if (!topics.some(topic => topic.trim())) {
            alert('Please add at least one topic');
            return;
        }
        if (!selectedTeacherIds.length) {
            alert('Please select at least one teacher');
            return;
        }

        try {
            const response = await axios.post('/db/subject-add', {
                subject: subjectName,
                topics: topics.filter(t => t.trim().length > 0),
                teachers: selectedTeacherIds
            });

            const data = await response.json();
            console.log('Subject creation response:', data);
            if (response.ok) {
                alert(`Success! Subject created:\n${JSON.stringify(data, null, 2)}`);
                // Navigate to dashboard
                props.setActiveSection('dashboard');
            } else {
                throw new Error(data.error || 'Failed to create subject');
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    }

    return (
        <div className="subject-creation-section">
        <h3>Subject Creation</h3>
        <form className="subject-form">
            <div className="form-group">
            <label htmlFor="subject-input">Subject Name</label>
            <input
                type="text"
                id="subject-input"
                name="subject"
                className="subject-input"
                placeholder="Enter subject name"
            />
            </div>

            <div className="form-group">
            <label htmlFor="topic-input">Topic Name</label>
            {/* Render dynamic topic inputs */}
            {topics.map((topic, index) => (
                <div key={`topic-${index}`} className="topic-input-row">
                <input
                    type="text"
                    id={`topic-input-${index}`}
                    name={`topic-${index}`}
                    placeholder={`Enter topic name ${index + 1}`}
                    value={topic}
                    className="topic-input"
                    onChange={(e) => updateTopic(index, e.target.value)}
                />
                {topic.length > 1 && (
                    <button
                    type="button"
                    onClick={() => removeTopic(index)}
                    className="remove-button"
                    aria-label={`Remove topic ${index + 1}`}
                    >
                    -
                    </button>
                )}
                </div>
            ))}
            <button 
                type="button"
                className="add-button"
                aria-label="Add topic"
                onClick={addTopic}>
                +
            </button>  
            </div>   
            
            <div className="form-group">
            <label htmlFor="teacher-input">Teachers</label>
            <div className="form-group">
                {loadingTeachers && <p> Loading teachers...</p>}
                {error && <p>{error}</p>}

                {!loadingTeachers && !error && (
                <div className="teacher-tabs">
                    {allTeachers.map(t => {
                    const tid = t.id;
                    const isSelected = selectedTeacherIds.includes(tid);
                    const isActive = activeTabId === tid;
                    return (
                        <button
                        key={tid}
                        type="button" 
                        id={`teacher-tab-${tid}`}
                        name={`teacher-${tid}-${t.name}`}
                        className={`teacher-tab ${isSelected ? 'selected' : ''} ${isActive ? 'active' : ''}`}
                        title={t.name}
                        onClick={() => {
                            setSelectedTeacherIds(prev => prev.includes(tid) ? prev.filter(id => id !== tid) : [...prev, tid]);
                            setActiveTabId(tid);
                        }}
                        >
                        {t.name}
                        </button>
                    )
                    })}
                </div>
                )}
            </div>
            </div>

            <div className="add-material-button">
            <button type="button" className="create-button" onClick={handleSubmitSubject}>
                Submit
            </button>
            </div>
        </form>
        </div>
    );
}

export default SubjectCreation;