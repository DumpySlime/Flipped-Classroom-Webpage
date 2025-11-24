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
            const response = await axios.post('auth/api/login', {
                username: state.username,
                password: state.password
            });
            
            // Extract tokens and user info from response
            const { access_token, user } = response.data;
            const token = access_token;
            
            // Store user info in localStorage and set token as dafult header
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
            localStorage.setItem('user', JSON.stringify(user));
            console.log("saved user info: ", JSON.stringify(localStorage.getItem('user'),null,2))
            setState(prevState => ({ ...prevState, error: '' }));
            
            // Call the onLogin callback to notify parent component
            if (onLogin) {
                onLogin(user.role, user);
            }
            
            alert(`Login successful! Welcome ${user.role === 'teacher' ? 'Teacher' : user.role === 'student' ? 'Student' : 'Admin'} ${user.firstName} ${user.lastName}`);
            
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
                <p>Admin: username = 'aa', password = 'aa'</p>
            </div>
        </div>
    )
}

export default Login;