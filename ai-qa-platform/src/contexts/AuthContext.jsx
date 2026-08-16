import { createContext, useContext, useState, useEffect } from 'react'
import { users } from '../data/mockData'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('qa_current_user')
    if (stored) {
      try {
        setCurrentUser(JSON.parse(stored))
      } catch {
        localStorage.removeItem('qa_current_user')
      }
    }
    setLoading(false)
  }, [])

  const login = (username, password) => {
    const user = users.find(u => u.username === username && u.password === password)
    if (!user) return { success: false, error: 'Invalid username or password' }
    if (user.status !== 'active') return { success: false, error: 'Account is deactivated. Contact admin.' }
    const userData = { id: user.id, username: user.username, name: user.name, email: user.email, role: user.role, avatar: user.avatar, joinedAt: user.joinedAt }
    setCurrentUser(userData)
    localStorage.setItem('qa_current_user', JSON.stringify(userData))
    return { success: true }
  }

  const logout = () => {
    setCurrentUser(null)
    localStorage.removeItem('qa_current_user')
  }

  const updateProfile = (updates) => {
    setCurrentUser(prev => ({ ...prev, ...updates }))
    localStorage.setItem('qa_current_user', JSON.stringify({ ...currentUser, ...updates }))
  }

  return (
    <AuthContext.Provider value={{ currentUser, login, logout, updateProfile, loading, isAdmin: currentUser?.role === 'admin' }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
