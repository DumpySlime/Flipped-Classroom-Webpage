import React, { useEffect, useState } from 'react'

function App() {

  const [data, setData] = useState([{}])
  
  useEffect(() => {
    fetch("/teacher/dashboard").then(
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

export default App;