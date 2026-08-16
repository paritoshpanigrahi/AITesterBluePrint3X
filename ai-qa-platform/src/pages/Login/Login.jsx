import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import './Login.css'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password')
      return
    }
    const result = login(username, password)
    if (result.success) navigate(from, { replace: true })
    else setError(result.error)
  }

  if (loading) return null

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">QA Test Platform</div>
          <p className="login-subtitle">Sign in to your account</p>
        </div>
        {error && <div className="login-error">{error}</div>}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input id="username" type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter username (admin, john, jane, etc.)" autoFocus />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter password" />
          </div>
          <button type="submit" className="login-btn">Sign In</button>
        </form>
        <div className="login-hint">
          <p><strong>Demo Credentials:</strong></p>
          <p>Admin: <code>admin</code> / <code>admin123</code></p>
          <p>User: <code>john</code> / <code>john123</code></p>
        </div>
      </div>
    </div>
  )
}
