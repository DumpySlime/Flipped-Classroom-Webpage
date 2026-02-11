import React, { useState } from 'react';
import axios from 'axios';
import "../styles.css";

function Login({ onLogin }) {
  const [state, setState] = useState({
    username: '',
    password: '',
    role: 'student',
    error: '',
    loading: false
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    
    setState(prevState => ({ ...prevState, loading: true, error: '' }));
    
    try {
      // Send login request to backend API
      const response = await axios.post('auth/api/login', {
        username: state.username,
        password: state.password
      });

      // Extract tokens and user info from response
      const { access_token, user } = response.data;
      
      // Store authentication data in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_id', user._id || user.id);
      localStorage.setItem('user_role', user.role);
      localStorage.setItem('user_firstname', user.firstName);
      localStorage.setItem('user_lastname', user.lastName);
      localStorage.setItem('user_username', user.username);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Set token as default header for future requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      console.log('Login successful. User info saved:', {
        id: user._id || user.id,
        role: user.role,
        name: `${user.firstName} ${user.lastName}`
      });

      setState(prevState => ({ 
        ...prevState, 
        error: '',
        loading: false 
      }));

      // Call the onLogin callback to notify parent component
      if (onLogin) {
        onLogin(user.role, user);
      }

      alert(`Login successful! Welcome ${
        user.role === 'teacher' ? 'Teacher' : 
        user.role === 'student' ? 'Student' : 
        'Admin'
      } ${user.firstName} ${user.lastName}`);

    } catch (err) {
      console.error("Login error:", err);
      
      let errorMessage = 'Invalid username or password';
      
      if (err.response) {
        // Server responded with error
        errorMessage = err.response.data.error || err.response.data.message || errorMessage;
      } else if (err.request) {
        // Request made but no response
        errorMessage = 'Cannot connect to server. Please check if backend is running.';
      }
      
      setState(prevState => ({ 
        ...prevState, 
        error: errorMessage,
        loading: false 
      }));
    }
  };

  const handleChange = (evt) => {
    const value = evt.target.value;
    setState({
      ...state,
      [evt.target.name]: value
    });
  };

  const handleOnSubmit = async (evt) => {
    evt.preventDefault();
    await handleLogin(evt);
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Login</h2>
        <form onSubmit={handleOnSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username:</label>
            <input
              type="text"
              id="username"
              name="username"
              value={state.username}
              onChange={handleChange}
              placeholder="Enter username"
              required
              disabled={state.loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              name="password"
              value={state.password}
              onChange={handleChange}
              placeholder="Enter password"
              required
              disabled={state.loading}
            />
          </div>

          {state.error && (
            <div className="error-message">
              {state.error}
            </div>
          )}

          <button 
            type="submit" 
            className="login-button"
            disabled={state.loading}
          >
            {state.loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="demo-credentials">
          <p><strong>Demo credentials:</strong></p>
          <ul>
            <li>Teacher: username = 'teacher', password = 'teacher'</li>
            <li>Student: username = 'student', password = 'student'</li>
            <li>Admin: username = 'aa', password = 'aa'</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Login;
