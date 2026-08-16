import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { products, orders, users, activities } from '../../data/mockData'
import './Dashboard.css'

export default function Dashboard() {
  const { currentUser, isAdmin } = useAuth()
  const navigate = useNavigate()

  const activeProducts = products.filter(p => p.status === 'active')
  const pendingOrders = orders.filter(o => o.status === 'pending')
  const recentOrders = [...orders].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, 5)
  const recentActivities = [...activities].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 6)

  const totalRevenue = orders.filter(o => o.status !== 'cancelled').reduce((s, o) => s + o.total, 0)
  const lowStockProducts = products.filter(p => p.status === 'active' && p.stock > 0 && p.stock <= 10)
  const recentUsers = [...users].sort((a, b) => new Date(b.joinedAt) - new Date(a.joinedAt)).slice(0, 5)
  const myTotalSpent = orders.filter(o => o.userId === currentUser.id).reduce((s, o) => s + o.total, 0)

  const orderStatusCounts = { pending: 0, processing: 0, shipped: 0, delivered: 0, cancelled: 0 }
  orders.forEach(o => { orderStatusCounts[o.status]++ })

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Welcome back, {currentUser?.name}</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-blue"><div className="stat-value">{activeProducts.length}</div><div className="stat-label">Active Products</div></div>
        <div className="stat-card stat-green"><div className="stat-value">{orders.length}</div><div className="stat-label">Total Orders</div></div>
        <div className="stat-card stat-yellow"><div className="stat-value">{pendingOrders.length}</div><div className="stat-label">Pending Orders</div></div>
        {isAdmin && <div className="stat-card stat-purple"><div className="stat-value">{users.length}</div><div className="stat-label">Total Users</div></div>}
        {isAdmin && <div className="stat-card stat-red"><div className="stat-value">${totalRevenue.toFixed(2)}</div><div className="stat-label">Total Revenue</div></div>}
        {isAdmin && <div className="stat-card stat-orange"><div className="stat-value">{lowStockProducts.length}</div><div className="stat-label">Low Stock Items</div></div>}
        {!isAdmin && <div className="stat-card stat-purple"><div className="stat-value">${myTotalSpent.toFixed(2)}</div><div className="stat-label">My Total Spent</div></div>}
      </div>

      {isAdmin && (
        <>
          <div className="quick-actions">
            <button className="qa-btn qa-blue" onClick={() => navigate('/products')}><span className="qa-icon">+</span> Add Product</button>
            <button className="qa-btn qa-green" onClick={() => navigate('/orders')}><span className="qa-icon">&#9998;</span> Manage Orders</button>
            <button className="qa-btn qa-purple" onClick={() => navigate('/users')}><span className="qa-icon">&#9783;</span> Manage Users</button>
            <button className="qa-btn qa-orange" onClick={() => navigate('/products')}><span className="qa-icon">&#9881;</span> Inventory</button>
          </div>

          {lowStockProducts.length > 0 && (
            <div className="d-card warning-card" style={{ marginBottom: 20 }}>
              <div className="d-card-header"><h2 style={{ color: '#dc2626' }}>Low Stock Alert</h2></div>
              <div className="d-card-body">
                <table className="d-table">
                  <thead><tr><th>Product</th><th>Stock</th><th>Category</th><th>Status</th></tr></thead>
                  <tbody>
                    {lowStockProducts.map(p => (
                      <tr key={p.id}>
                        <td className="order-id">{p.name}</td>
                        <td style={{ color: p.stock === 0 ? '#dc2626' : '#f59e0b', fontWeight: 600 }}>{p.stock}</td>
                        <td>{p.category}</td>
                        <td><span className={`badge badge-${p.status}`}>{p.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      <div className="dashboard-grid">
        <div className="d-card">
          <div className="d-card-header"><h2>Recent Orders</h2></div>
          <div className="d-card-body">
            {recentOrders.length === 0 ? <p className="empty-text">No orders yet</p> : (
              <table className="d-table">
                <thead><tr><th>Order ID</th><th>Total</th><th>Status</th><th>Date</th></tr></thead>
                <tbody>
                  {recentOrders.map(o => (
                    <tr key={o.id}>
                      <td className="order-id">{o.id}</td>
                      <td>${o.total.toFixed(2)}</td>
                      <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                      <td>{o.createdAt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="d-card">
          <div className="d-card-header"><h2>Recent Activity</h2></div>
          <div className="d-card-body">
            {recentActivities.length === 0 ? <p className="empty-text">No recent activity</p> : (
              <div className="activity-feed">
                {recentActivities.map(a => (
                  <div key={a.id} className="activity-item">
                    <div className={`activity-dot dot-${a.type}`} />
                    <div className="activity-content">
                      <p className="activity-message">{a.message}</p>
                      <span className="activity-time">{a.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {isAdmin && (
        <div className="dashboard-grid" style={{ marginTop: 20 }}>
          <div className="d-card">
            <div className="d-card-header"><h2>Order Distribution</h2></div>
            <div className="d-card-body">
              <div className="order-dist">
                {Object.entries(orderStatusCounts).map(([status, count]) => (
                  <div key={status} className="dist-row">
                    <span className={`badge badge-${status}`}>{status}</span>
                    <div className="dist-bar-wrap">
                      <div className={`dist-bar bar-${status}`} style={{ width: `${orders.length > 0 ? (count / orders.length) * 100 : 0}%` }} />
                    </div>
                    <span className="dist-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="d-card">
            <div className="d-card-header"><h2>Recent Registrations</h2></div>
            <div className="d-card-body">
              {recentUsers.length === 0 ? <p className="empty-text">No users</p> : (
                <div className="reg-list">
                  {recentUsers.map(u => (
                    <div key={u.id} className="reg-item">
                      <div className="user-avatar-sm">{u.name.charAt(0).toUpperCase()}</div>
                      <div className="reg-info">
                        <span className="reg-name">{u.name}</span>
                        <span className="reg-role">{u.role} &middot; Joined {u.joinedAt}</span>
                      </div>
                      <span className={`badge badge-${u.status}`}>{u.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
