import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export default function ProtectedRoute({ children, requiredRole }) {
  const { currentUser, isAdmin, loading } = useAuth()
  const location = useLocation()

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /></div>
  if (!currentUser) return <Navigate to="/login" state={{ from: location }} replace />
  if (requiredRole === 'admin' && !isAdmin) return <Navigate to="/dashboard" replace />

  return children
}
