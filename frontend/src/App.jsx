import React, { useState, useEffect } from 'react'
import './styles.css'
import Login from './component/Login.jsx'

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userRole, setUserRole] = useState('');
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    // Check if user is logged in by verifying token in localStorage
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setIsLoggedIn(true);
        setUserRole(parsedUser.role);
        setUserInfo(parsedUser);
      } catch (error) {
        console.error('Error parsing user data from localStorage:', error);
        setIsLoggedIn(false);
        setUserRole('');
        setUserInfo(null);
      }
    }
  }, []);

  // Function to handle successful login
  const handleLogin = (role) => {
    setIsLoggedIn(true);
    setUserRole(role);
  };

  // Function to handle logout
  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserRole('');
    setUserInfo(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  return (
    <div className="app-container">
      {isLoggedIn ? (
        userRole === 'teacher' ? (
          <div>
            <h1>Flipped Classroom System</h1>
            <p>Teacher Dashboard coming soon!</p>
            <button className="logout-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        ) : (
          <div>
            <h1>Flipped Classroom System</h1>
            <p>Student Dashboard coming soon!</p>
            <button className="logout-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        )
      ) : (
        <>
          <h1>Flipped Classroom System</h1>
          <Login onLogin={handleLogin} />
        </>
      )}
    </div>
  )
}