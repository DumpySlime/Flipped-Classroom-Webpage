import { useState } from 'react'
import './styles.css'
import Login from './component/Login.js'

export default function App() {

  const [data, setData] = useState([{}])
  
  useEffect(() => {
    fetch("/auth").then(
      res => res.json()
    ).then(
      data => {
        setData(data)
        console.log(data)
      }
    )
  }, [])

  return (
    <div>
      {(typeof data.message === 'undefined') ? (
        <p>Loading...</p>
      ) : (
        <h1>{data.message}</h1>
      )}
    </div>
  )
}