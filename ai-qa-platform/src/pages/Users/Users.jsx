import { useState } from 'react'
import { users as initialUsers } from '../../data/mockData'
import './Users.css'

export default function Users() {
  const [userList, setUserList] = useState(initialUsers)
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [form, setForm] = useState({ username: '', password: '', name: '', email: '', role: 'user', status: 'active' })

  const filtered = userList.filter(u => u.name.toLowerCase().includes(search.toLowerCase()) || u.username.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()))

  const resetForm = () => setForm({ username: '', password: '', name: '', email: '', role: 'user', status: 'active' })

  const openAdd = () => { setEditingUser(null); resetForm(); setShowModal(true) }

  const openEdit = (u) => {
    setEditingUser(u)
    setForm({ username: u.username, password: '', name: u.name, email: u.email, role: u.role, status: u.status })
    setShowModal(true)
  }

  const handleSave = (e) => {
    e.preventDefault()
    if (!form.username || !form.name || !form.email) return
    if (editingUser) {
      setUserList(prev => prev.map(u => u.id === editingUser.id ? { ...u, username: form.username, name: form.name, email: form.email, role: form.role, status: form.status } : u))
    } else {
      if (!form.password) return
      if (userList.some(u => u.username === form.username)) { alert('Username already exists'); return }
      const newId = Math.max(...userList.map(u => u.id), 0) + 1
      setUserList(prev => [...prev, { id: newId, username: form.username, password: form.password, name: form.name, email: form.email, role: form.role, status: form.status, avatar: null, joinedAt: new Date().toISOString().slice(0, 10) }])
    }
    setShowModal(false)
    resetForm()
  }

  const toggleStatus = (id) => {
    setUserList(prev => prev.map(u => u.id === id ? { ...u, status: u.status === 'active' ? 'inactive' : 'active' } : u))
  }

  const handleDelete = (id) => {
    if (!confirm('Delete this user?')) return
    setUserList(prev => prev.filter(u => u.id !== id))
  }

  return (
    <div className="users-page">
      <div className="page-header"><h1>Users</h1><p>Manage all registered users</p></div>

      <div className="toolbar">
        <div className="toolbar-left">
          <input className="search-input" type="text" placeholder="Search users..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={openAdd}>+ Add User</button>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); resetForm() }}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h2>{editingUser ? 'Edit User' : 'Add User'}</h2><button className="modal-close" onClick={() => { setShowModal(false); resetForm() }}>&times;</button></div>
            <form onSubmit={handleSave}>
              <div className="modal-body">
                <div className="form-row">
                  <div className="form-group"><label>Username</label><input type="text" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} required /></div>
                  <div className="form-group"><label>Password {editingUser && '(leave blank to keep)'}</label><input type="password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required={!editingUser} /></div>
                </div>
                <div className="form-row">
                  <div className="form-group"><label>Full Name</label><input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required /></div>
                  <div className="form-group"><label>Email</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required /></div>
                </div>
                <div className="form-row">
                  <div className="form-group"><label>Role</label><select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}><option value="user">User</option><option value="admin">Admin</option></select></div>
                  <div className="form-group"><label>Status</label><select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}><option value="active">Active</option><option value="inactive">Inactive</option></select></div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowModal(false); resetForm() }}>Cancel</button>
                <button type="submit" className="btn btn-primary">{editingUser ? 'Update' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="users-table-wrap">
        <table className="users-table">
          <thead>
            <tr><th>User</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? <tr><td colSpan={7} className="empty-text">No users found</td></tr> : (
              filtered.map(u => (
                <tr key={u.id}>
                  <td><div className="user-cell"><div className="user-avatar-sm">{u.name.charAt(0).toUpperCase()}</div><span>{u.name}</span></div></td>
                  <td>{u.username}</td>
                  <td>{u.email}</td>
                  <td><span className={`badge-role badge-role-${u.role}`}>{u.role}</span></td>
                  <td><span className={`badge badge-${u.status}`}>{u.status}</span></td>
                  <td>{u.joinedAt}</td>
                  <td>
                    <div className="action-btns">
                      <button className="btn btn-sm btn-secondary" onClick={() => openEdit(u)}>Edit</button>
                      <button className={`btn btn-sm ${u.status === 'active' ? 'btn-warning' : 'btn-success'}`} onClick={() => toggleStatus(u.id)}>{u.status === 'active' ? 'Deactivate' : 'Activate'}</button>
                      <button className="btn btn-sm btn-danger" onClick={() => handleDelete(u.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
