import { useState } from 'react';
import axios from 'axios';
import '../../styles.css';
import '../../dashboard.css';

function AddUser(props) {
  const [values, setValues] = useState({
    username: '',
    password: '',
    firstName: '',
    lastName: '',
    role: ''
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleChanges = (e) => {
    setValues({ ...values, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    console.log('Form submitted with values:', values);

    // Validate role is selected
    if (!values.role) {
      setError('Please select a role');
      return;
    }

    // Get JWT token from localStorage
    const token = localStorage.getItem('access_token');

    // Send as JSON (matching backend expectation)
    axios.post('http://localhost:5000/db/user-add', {
      username: values.username,
      password: values.password,
      firstName: values.firstName,
      lastName: values.lastName,
      role: values.role
    }, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })
      .then(function (response) {
        console.log('User added successfully:', response.data);
        setSuccess(`User "${values.username}" added successfully as ${values.role}!`);
        
        // Reset form
        setValues({
          username: '',
          password: '',
          firstName: '',
          lastName: '',
          role: ''
        });
        
        // Only call setActiveSection if it exists
        if (props.setActiveSection && typeof props.setActiveSection === 'function') {
          setTimeout(() => {
            props.setActiveSection('overview');
          }, 1500);
        }
      })
      .catch(function (error) {
        console.error('Error adding user:', error);
        const errorMsg = error.response?.data?.error || 'Failed to add user';
        setError(errorMsg);
      });
  };

  return (
    <div className="content-section">
      <h2>Add New User</h2>
      
      {error && (
        <div className="alert alert-error" style={{ 
          padding: '10px', 
          marginBottom: '15px', 
          backgroundColor: '#fee', 
          border: '1px solid #fcc',
          borderRadius: '4px',
          color: '#c33'
        }}>
          {error}
        </div>
      )}
      
      {success && (
        <div className="alert alert-success" style={{ 
          padding: '10px', 
          marginBottom: '15px', 
          backgroundColor: '#efe', 
          border: '1px solid #cfc',
          borderRadius: '4px',
          color: '#3c3'
        }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="user-form">
        <div className="form-group">
          <label htmlFor="username">Username:</label>
          <input
            type="text"
            id="username"
            name="username"
            value={values.username}
            onChange={handleChanges}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            name="password"
            value={values.password}
            onChange={handleChanges}
            required
            minLength="6"
          />
        </div>

        <div className="form-group">
          <label htmlFor="firstName">First Name:</label>
          <input
            type="text"
            id="firstName"
            name="firstName"
            value={values.firstName}
            onChange={handleChanges}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="lastName">Last Name:</label>
          <input
            type="text"
            id="lastName"
            name="lastName"
            value={values.lastName}
            onChange={handleChanges}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="role">Role: *</label>
          <select
            id="role"
            name="role"
            value={values.role}
            onChange={handleChanges}
            required
          >
            <option value="">-- Select Role --</option>
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <button type="submit" className="submit-btn">
          Add User
        </button>
      </form>
    </div>
  );
}

export default AddUser;
