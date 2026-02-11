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
	const handleLogin = (role, user) => {
		setIsLoggedIn(true);
		setUserRole(role);
		setUserInfo(user);
	};

	const handleLogout = () => {
		setIsLoggedIn(false);
		setUserRole('');
		setUserInfo(null);
		localStorage.clear();
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