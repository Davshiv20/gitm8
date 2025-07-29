import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {


  const [username, setUsername] = useState('');
  const [userInfo, setUserInfo] = useState<{ name?: string; bio?: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUsername(e.target.value);
  };

  const handleGetUser = async () => {
    setLoading(true);
    setError(null);
    setUserInfo(null);
    try {
      const response = await fetch(`http://127.0.0.1:8000/users/${encodeURIComponent(username)}`);
      if (!response.ok) {
        throw new Error('User not found');
      }
      const data = await response.json();
      setUserInfo({ name: data.name, bio: data.bio });
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1>gitm8</h1>
      <div className="input-container">
        <input
          type="text"
          placeholder="Enter your github username"
          value={username}
          onChange={handleInputChange}
        />
        <button onClick={handleGetUser} disabled={loading || !username.trim()}>
          {loading ? 'Loading...' : 'Get User'}
        </button>
      </div>
      <div className="output-container">
        <h2>User Information</h2>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {userInfo ? (
          <>
            <p>Name: <span id="name">{userInfo.name || 'N/A'}</span></p>
            <p>Bio: <span id="bio">{userInfo.bio || 'N/A'}</span></p>
          </>
        ) : (
          <p>No user info loaded.</p>
        )}
      </div>
    </>
  )
}

export default App
