import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import './Profile.css'

export default function Profile() {
  const { currentUser, updateProfile } = useAuth()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ name: currentUser.name, email: currentUser.email })
  const [saved, setSaved] = useState(false)

  const handleSave = (e) => {
    e.preventDefault()
    if (!form.name.trim() || !form.email.trim()) return
    updateProfile({ name: form.name, email: form.email })
    setEditing(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="profile-page">
      <div className="page-header"><h1>My Profile</h1><p>View and edit your profile information</p></div>

      <div className="profile-card">
        <div className="profile-avatar-section">
          <div className="profile-avatar-lg">{currentUser.name?.charAt(0)?.toUpperCase()}</div>
          <div>
            <h2>{currentUser.name}</h2>
            <span className={`user-role role-${currentUser.role}`}>{currentUser.role}</span>
          </div>
        </div>

        {saved && <div className="success-message">Profile updated successfully!</div>}

        {editing ? (
          <form onSubmit={handleSave} className="profile-form">
            <div className="form-group"><label>Full Name</label><input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required /></div>
            <div className="form-group"><label>Email Address</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required /></div>
            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={() => { setEditing(false); setForm({ name: currentUser.name, email: currentUser.email }) }}>Cancel</button>
              <button type="submit" className="btn btn-primary">Save Changes</button>
            </div>
          </form>
        ) : (
          <div className="profile-details">
            <div className="detail-row"><span className="detail-label">Username</span><span>{currentUser.username}</span></div>
            <div className="detail-row"><span className="detail-label">Email</span><span>{currentUser.email}</span></div>
            <div className="detail-row"><span className="detail-label">Role</span><span className={`badge-role badge-role-${currentUser.role}`}>{currentUser.role}</span></div>
            <div className="detail-row"><span className="detail-label">Member Since</span><span>{currentUser.joinedAt}</span></div>
            <button className="btn btn-primary" onClick={() => setEditing(true)}>Edit Profile</button>
          </div>
        )}
      </div>
    </div>
  )
}
