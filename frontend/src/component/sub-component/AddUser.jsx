import { useState } from 'react';
import '../../styles.css';
import '../../dashboard.css';

function AddUser() {

    const [values, setValues] = useState({
        username: '',
        password: '',
        firstName: '',
        lastName: '',
        role: ''
    })

    const handleChanges = (e) => {
        setValues({...values, [e.target.name]:[e.target.value]})
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log('Form submitted with values:', values);

        try {
            const response = await fetch('/admin/api/user/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(values)
            })
            
            if (response.ok) {
                console.log('User added successfully:', await response.json());
            }
        } catch (error) {
            console.error('Error adding user:', error);
        }
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
                        name="first-name"
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
                        name="last-name"
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