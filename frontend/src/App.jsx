import { useState, useEffect } from 'react'
import axios from 'axios'
import './styles.css'
import Login from './component/Login.jsx'
import Dashboard from './component/Dashboard.jsx'

export default function App() {
	const [isLoggedIn, setIsLoggedIn] = useState(false);
	const [userRole, setUserRole] = useState('');
	const [userInfo, setUserInfo] = useState(null);

	useEffect(() => {
		// Check if user is logged in by verifying token in sessionStorage
		const token = sessionStorage.getItem('access_token');
		const userData = sessionStorage.getItem('user');
		
		if (token && userData) {
		try {
			const parsedUser = JSON.parse(userData);
			setIsLoggedIn(true);
			setUserRole(parsedUser.role);
			setUserInfo(parsedUser);
		} catch (error) {
			console.error('Error parsing user data from sessionStorage:', error);
			setIsLoggedIn(false);
			setUserRole('');
			setUserInfo(null);
		}
		}
	}, []);

	// Function to handle successful login
	const handleLogin = (role, user) => {
		setIsLoggedIn(true);
		setUserRole(role);
		setUserInfo(user);
	};

	const handleLogout = () => {
		setIsLoggedIn(false);
		setUserRole('');
		setUserInfo(null);
		// Clear sessionStorage
		sessionStorage.removeItem('access_token');
		sessionStorage.removeItem('user_id');
		sessionStorage.removeItem('user_role');
		sessionStorage.removeItem('user_firstname');
		sessionStorage.removeItem('user_lastname');
		sessionStorage.removeItem('user_username');
		sessionStorage.removeItem('user');
		delete axios.defaults.headers.common['Authorization'];
		window.location.href = '/';
	};

	return (
		<div className="app-container">
		{isLoggedIn ? (
			<Dashboard userRole={userRole} userInfo={userInfo} onLogout={handleLogout} />
		) : (
			<Login onLogin={handleLogin} />
		)}
		</div>
	)
}
