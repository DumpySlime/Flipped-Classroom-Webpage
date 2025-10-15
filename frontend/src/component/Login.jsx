import React, { useState } from 'react';
import axios from 'axios';
import "../styles.css"

function Login({ onLogin }) {
    
    const [state, setState] = useState({
        username: '',
        password: '',
        role: 'student',
        error: ''
    });

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            // Send login request to backend API
            const response = await axios.post('/api/login', {
                username: state.username,
                password: state.password
            });
            
            // Extract tokens and user info from response
            const { access_token, user } = response.data;
            const token = access_token;
            
            // Store tokens and user info in localStorage
            localStorage.setItem('token', token);
            localStorage.setItem('user', JSON.stringify(user));
            
            setState(prevState => ({ ...prevState, error: '' }));
            
            // Call the onLogin callback to notify parent component
            if (onLogin) {
                onLogin(user.role);
            }
            
            alert(`Login successful! Welcome ${user.role === 'teacher' ? 'Teacher' : 'Student'} ${user.firstName} ${user.lastName}`);
            
        } catch (err) {
            setState(prevState => ({ ...prevState, error: 'Invalid username or password' }));
            console.error("Login error:", err);
        }
    }

    const handleChange = evt => {
        const value = evt.target.value;
        setState({
            ...state,
            [evt.target.name]: value
        });
    };

    const handleOnSubmit = async (evt) => {
        await handleLogin(evt);
    };

    return (
        <div className="login-container">
            <h2>User Login</h2>
            <form onSubmit={handleOnSubmit} className="login-form">
                <div className="form-group">
                    <label htmlFor="role">Role</label>
                    <select
                        id="role"
                        name="role"
                        value={state.role}
                        onChange={handleChange}
                        className="role-select"
                    >
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                    </select>
                </div>
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        value={state.username}
                        onChange={handleChange}
                        placeholder="Please enter username"
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        value={state.password}
                        onChange={handleChange}
                        placeholder="Please enter password"
                        required
                    />
                </div>
                {state.error && <div className="error-message">{state.error}</div>}
                <button type="submit" className="login-button">Login</button>
            </form>
            
            {/* Demo credentials */}
            <div className="demo-credentials">
                <p>Demo credentials:</p>
                <p>Teacher: username = 'teacher', password = 'teacher'</p>
                <p>Student: username = 'student', password = 'student'</p>
            </div>
        </div>
    )
}

export default Login;