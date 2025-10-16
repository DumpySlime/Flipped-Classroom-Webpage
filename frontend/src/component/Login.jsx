import { useState } from "react";
import "../styles.css"

function Login() {
    
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post("/auth/api/login", { username, password });
            console.log(response.data);
            // Handle successful login (e.g., store tokens, redirect, etc.)
            
            const { token, role } = response.data;

            localStorage.setItem('token', token)
            setError('')

        } catch (err) {
            // Handle login error
            setError('Invalid ')
        }
    }

    useEffect(() => {
        const place = {
            state
        }
        axios.post("auth/api/login", {username, password})


    })

    const handleChange = evt => {
        const value = evt.target.value;
        setState({
            ...state,
            [evt.target.name]: value
        });
    };

    const handleOnSubmit = evt => {
        evt.preventDefault()

        const {username, password} = state;
        alert(`You are login with username: ${username} and password: ${password}`);

        for (const key in state) {
            setState({
                ...state,
                [key]: ""
            })
        }
    };

    return (
        <div className="form-container sign-in-container">
            <form onSubmit={handleOnSubmit}>
                <input
                    type="text"
                    placeholder="Username"
                    name="username"
                    value={state.username}
                    onChange={handleChange}
                />
                <input
                    type="password"
                    placeholder="Password"
                    name="password"
                    value={state.password}
                    onChange={handleChange}
                />
                <button>Sign In</button>
            </form>            
        </div>
    )
}

export default Login();