import { useState, useEffect } from 'react';
import '../../styles.css';
import '../../dashboard.css';
import axios from 'axios';

function AvatarInitials({ firstName, lastName }) {
  const initials = `${(firstName || '').charAt(0)}${(lastName || '').charAt(0)}`.toUpperCase();
  return <div className="sm-avatar">{initials}</div>;
}

function RoleBadge({ role }) {
  return <span className={`sm-role-badge sm-role-${role}`}>{role}</span>;
}

function SubjectMembers(props) {
  const { userInfo, userRole } = props;

  const [subjects, setSubjects] = useState([]); // array of subject objects (id, subject, ...)
  const [membersBySubject, setMembersBySubject] = useState({}); // { subjectId: [members] }
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    setError(null);

    // helper to handle axios errors and cancellation
    const isCanceled = (err) => err?.name === 'CanceledError' || err?.message === 'canceled';

    if (userRole === 'admin') {
      // Admin: fetch all subject members in one call
      console.log('SubjectMembers: fetching all subject members (admin)');
      axios.get('/db/subjectmembers', { signal: ac.signal })
        .then(res => {
          const subjectmembers = res.data?.subjectmembers || [];
          // build subjects list and membersBySubject map
          const subjectsMap = {};
          const grouped = {};
          subjectmembers.forEach(m => {
            const sid = m.subject_id;
            if (!subjectsMap[sid]) {
              subjectsMap[sid] = { id: sid, subject: m.subject };
            }
            if (!grouped[sid]) grouped[sid] = [];
            grouped[sid].push(m);
          });
          setSubjects(Object.values(subjectsMap));
          setMembersBySubject(grouped);
          setLoading(false);
        })
        .catch(err => {
          if (!isCanceled(err)) {
            console.error('Error fetching subject members (admin):', err);
            setError('Failed to load subject members.');
            setLoading(false);
          }
        });

    } else if (userRole === 'teacher') {
      // Teacher: first fetch subjects assigned to this teacher, then fetch members per subject
      console.log(`SubjectMembers: fetching subjects for teacher ${userInfo?.id}`);
      axios.get('/db/subject', {
        params: { teacher_id: userInfo?.id },
        signal: ac.signal
      })
      .then(res => {
        const fetchedSubjects = res.data?.subjects || [];
        setSubjects(fetchedSubjects);

        // For each subject, fetch its members
        return Promise.all(fetchedSubjects.map(s => {
          console.log(`SubjectMembers: fetching members for subject ${s.id}`);
          return axios.get('/db/subjectmembers', {
            params: { subject_id: s.id },
            signal: ac.signal
          })
          .then(resp => {
            const members = resp.data?.subjectmembers || [];
            // For teacher view, students list only
            const studentsOnly = members.filter(m => m.role === 'student');
            return { subjectId: s.id, members: studentsOnly };
          })
          .catch(err => {
            if (!isCanceled(err)) {
              console.error(`Error fetching members for subject ${s.id}:`, err);
            }
            return { subjectId: s.id, members: [] };
          });
        }));
      })
      .then(results => {
        // results is array of { subjectId, members }
        const grouped = results.reduce((acc, cur) => {
          acc[cur.subjectId] = cur.members;
          return acc;
        }, {});
        setMembersBySubject(grouped);
        setLoading(false);
      })
      .catch(err => {
        if (!isCanceled(err)) {
          console.error('Error fetching teacher subjects or members:', err);
          setError('Failed to load subject members.');
          setLoading(false);
        }
      });

    } else {
      // Other roles (student or unknown) — show nothing or a message
      setSubjects([]);
      setMembersBySubject({});
      setLoading(false);
    }

    return () => ac.abort();
  }, [userInfo?.id, userRole]);

  // Debug logging similar to your template
  useEffect(() => {
    console.log('SubjectMembers subjects:', JSON.stringify(subjects, null, 2));
    console.log('SubjectMembers membersBySubject:', JSON.stringify(membersBySubject, null, 2));
  }, [subjects, membersBySubject]);

  const renderMemberRow = (m) => (
    <div key={m._id} className="sm-member-row">
      <div className="sm-left">
        <AvatarInitials firstName={m.firstName} lastName={m.lastName} />
        <div className="sm-name-block">
          <div className="sm-name">{m.firstName} {m.lastName}</div>
          <div className="sm-subtext">Member</div>
        </div>
      </div>
      <div className="sm-right">
        <RoleBadge role={m.role} />
      </div>
    </div>
  );

  if (loading) return <div className="sm-loading">Loading subject members…</div>;
  if (error) return <div className="sm-error">{error}</div>;
  if (subjects.length === 0) return <div className="sm-empty">There is no subject assigned</div>;

  return (
    <div className="sm-container">
      {subjects.length === 1 ? (
        <div className="sm-single">
          <div className="sm-subject-header">
            <h3 className="sm-subject-title">{subjects[0].subject || subjects[0].name}</h3>
            <div className="sm-subject-count">{(membersBySubject[subjects[0].id || subjects[0]._id] || []).length} members</div>
          </div>
          <div className="sm-list">
            {(membersBySubject[subjects[0].id || subjects[0]._id] || []).map(renderMemberRow)}
          </div>
        </div>
      ) : (
        <div className="sm-multi">
          {subjects.map(s => {
            const sid = s.id || s._id;
            const members = membersBySubject[sid] || [];
            return (
              <div key={sid} className="sm-subject-card">
                <div className="sm-subject-card-header">
                  <div className="sm-subject-title-small">{s.subject || s.name}</div>
                  <div className="sm-subject-count-small">{members.length} members</div>
                </div>
                <div className="sm-list">
                  {members.length === 0 ? <div className="sm-no-members">No members</div> : members.map(renderMemberRow)}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default SubjectMembers;
