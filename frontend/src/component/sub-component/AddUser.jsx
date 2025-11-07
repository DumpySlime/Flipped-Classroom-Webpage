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
    })

    const handleChanges = (e) => {
        setValues({...values, [e.target.name]: e.target.value })
    }

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Form submitted with values:', values);
        axios.post('/db/user-add', values)
        .then(function (response) {
            console.log(`User added successfully: ${response.data}`);
            setValues({
                username: '',
                password: '',
                firstName: '',
                lastName: '',
                role: ''
            })
        })
        .catch(function (error) {
            console.log(`Error adding user: ${error}`);
        });
    }

    return (
        <div className="user-creation-section">
            <h3>User Creation</h3>
            <form className="user-form" onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        className="user-input"
                        placeholder="Enter Username"
                        onChange={(e) => handleChanges(e)}
                        required
                        value={values.username}
                    />
                    
                    <label htmlFor="password">Password</label>
                    <input
                        type="text"
                        id="password"
                        name="password"
                        className="user-input"
                        placeholder="Enter Password"
                        onChange={(e) => handleChanges(e)}
                        required
                        value={values.password}
                    />

                    <label htmlFor="first-name">First Name</label>
                    <input
                        type="text"
                        id="first-name"
                        name="firstName"
                        className="user-input"
                        placeholder="Enter First Name"
                        onChange={(e) => handleChanges(e)}
                        required
                        value={values.firstName}
                    />

                    <label htmlFor="last-name">Last Name</label>
                    <input
                        type="text"
                        id="last-name"
                        name="lastName"
                        className="user-input"
                        placeholder="Enter Last Name"
                        onChange={(e) => handleChanges(e)}
                        required
                        value={values.lastName}
                    />

                    <label htmlFor="role">Role</label>
                    <select id="role" name="role" className="user-input" onChange={(e) => handleChanges(e)} required value={values.role}>
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <button type="submit" className="submit-button">Add User</button>
            </form>
        </div>
    );
}

export default AddUser;