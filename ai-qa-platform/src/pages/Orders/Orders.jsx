import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { orders as initialOrders, products, users, orderStatuses } from '../../data/mockData'
import './Orders.css'

export default function Orders() {
  const { currentUser, isAdmin } = useAuth()
  const [orderList, setOrderList] = useState(initialOrders)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [newOrder, setNewOrder] = useState({ userId: currentUser.id, items: [{ productId: '', quantity: 1 }], shippingAddress: '', paymentMethod: 'Credit Card' })

  const filtered = orderList.filter(o => {
    if (!isAdmin && o.userId !== currentUser.id) return false
    const matchStatus = !statusFilter || o.status === statusFilter
    const matchSearch = o.id.toLowerCase().includes(search.toLowerCase())
    return matchStatus && matchSearch
  })

  const getProductName = (id) => products.find(p => p.id === id)?.name || 'Unknown'
  const getUserName = (id) => users.find(u => u.id === id)?.name || 'Unknown'

  const openDetail = (order) => setSelectedOrder(order)

  const updateStatus = (orderId, newStatus) => {
    setOrderList(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus, updatedAt: new Date().toISOString().slice(0, 10) } : o))
    if (selectedOrder?.id === orderId) setSelectedOrder(prev => ({ ...prev, status: newStatus }))
  }

  const handleAddOrder = (e) => {
    e.preventDefault()
    const validItems = newOrder.items.filter(i => i.productId && i.quantity > 0)
    if (validItems.length === 0 || !newOrder.shippingAddress.trim()) return

    const total = validItems.reduce((sum, i) => {
      const p = products.find(pr => pr.id === parseInt(i.productId))
      return sum + (p ? p.price * i.quantity : 0)
    }, 0)

    const newId = `ORD-${String(orderList.length + 1).padStart(3, '0')}`
    setOrderList(prev => [{
      id: newId, userId: currentUser.id, items: validItems.map(i => ({ productId: parseInt(i.productId), quantity: parseInt(i.quantity) })),
      total, status: 'pending', shippingAddress: newOrder.shippingAddress, paymentMethod: newOrder.paymentMethod,
      createdAt: new Date().toISOString().slice(0, 10), updatedAt: new Date().toISOString().slice(0, 10)
    }, ...prev])
    setShowModal(false)
    setNewOrder({ userId: currentUser.id, items: [{ productId: '', quantity: 1 }], shippingAddress: '', paymentMethod: 'Credit Card' })
  }

  const addItemRow = () => setNewOrder(o => ({ ...o, items: [...o.items, { productId: '', quantity: 1 }] }))
  const updateItem = (idx, field, value) => setNewOrder(o => ({ ...o, items: o.items.map((item, i) => i === idx ? { ...item, [field]: value } : item) }))
  const removeItem = (idx) => setNewOrder(o => ({ ...o, items: o.items.filter((_, i) => i !== idx) }))

  return (
    <div className="orders-page">
      <div className="page-header"><h1>Orders</h1><p>{isAdmin ? 'Manage all orders' : 'View your orders'}</p></div>

      <div className="toolbar">
        <div className="toolbar-left">
          <input className="search-input" type="text" placeholder="Search by order ID..." value={search} onChange={e => setSearch(e.target.value)} />
          <select className="filter-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            {orderStatuses.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
          </select>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ New Order</button>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal modal-lg" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h2>Create New Order</h2><button className="modal-close" onClick={() => setShowModal(false)}>&times;</button></div>
            <form onSubmit={handleAddOrder}>
              <div className="modal-body">
                <div className="form-group"><label>Shipping Address</label><input type="text" value={newOrder.shippingAddress} onChange={e => setNewOrder(o => ({ ...o, shippingAddress: e.target.value }))} required placeholder="Enter shipping address" /></div>
                <div className="form-group"><label>Payment Method</label><select value={newOrder.paymentMethod} onChange={e => setNewOrder(o => ({ ...o, paymentMethod: e.target.value }))}><option>Credit Card</option><option>Debit Card</option><option>PayPal</option></select></div>
                <div className="form-group"><label>Order Items</label>
                  {newOrder.items.map((item, idx) => (
                    <div key={idx} className="order-item-row">
                      <select value={item.productId} onChange={e => updateItem(idx, 'productId', e.target.value)} required>
                        <option value="">Select product...</option>
                        {products.filter(p => p.status === 'active').map(p => <option key={p.id} value={p.id}>{p.name} - ${p.price.toFixed(2)}</option>)}
                      </select>
                      <input type="number" min="1" value={item.quantity} onChange={e => updateItem(idx, 'quantity', e.target.value)} className="qty-input" />
                      {newOrder.items.length > 1 && <button type="button" className="btn btn-danger btn-sm" onClick={() => removeItem(idx)}>X</button>}
                    </div>
                  ))}
                  <button type="button" className="btn btn-secondary btn-sm" onClick={addItemRow} style={{ marginTop: 8 }}>+ Add Item</button>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Place Order</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedOrder && (
        <div className="modal-overlay" onClick={() => setSelectedOrder(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h2>Order {selectedOrder.id}</h2><button className="modal-close" onClick={() => setSelectedOrder(null)}>&times;</button></div>
            <div className="modal-body">
              <p><strong>Customer:</strong> {getUserName(selectedOrder.userId)}</p>
              <p><strong>Total:</strong> ${selectedOrder.total.toFixed(2)}</p>
              <p><strong>Status:</strong> <span className={`badge badge-${selectedOrder.status}`}>{selectedOrder.status}</span></p>
              <p><strong>Payment:</strong> {selectedOrder.paymentMethod}</p>
              <p><strong>Shipping:</strong> {selectedOrder.shippingAddress}</p>
              <p><strong>Created:</strong> {selectedOrder.createdAt}</p>
              <h4 style={{ margin: '16px 0 8px' }}>Items</h4>
              {selectedOrder.items.map((item, idx) => (
                <div key={idx} className="order-item-row" style={{ borderBottom: '1px solid #f0f0f5', padding: '6px 0' }}>
                  <span>{getProductName(item.productId)}</span>
                  <span style={{ color: '#6b7280', fontSize: 13 }}>x{item.quantity}</span>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              {isAdmin && selectedOrder.status !== 'delivered' && selectedOrder.status !== 'cancelled' && (
                <div style={{ display: 'flex', gap: 8, marginRight: 'auto' }}>
                  {selectedOrder.status === 'pending' && <button className="btn btn-primary" onClick={() => updateStatus(selectedOrder.id, 'processing')}>Process</button>}
                  {selectedOrder.status === 'processing' && <button className="btn btn-primary" onClick={() => updateStatus(selectedOrder.id, 'shipped')}>Ship</button>}
                  {selectedOrder.status === 'shipped' && <button className="btn btn-primary" onClick={() => updateStatus(selectedOrder.id, 'delivered')}>Deliver</button>}
                  {selectedOrder.status !== 'cancelled' && <button className="btn btn-danger" onClick={() => updateStatus(selectedOrder.id, 'cancelled')}>Cancel</button>}
                </div>
              )}
              <button className="btn btn-secondary" onClick={() => setSelectedOrder(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      <div className="orders-list">
        {filtered.length === 0 ? <p className="empty-text">No orders found</p> : (
          filtered.map(o => (
            <div key={o.id} className="order-card" onClick={() => openDetail(o)}>
              <div className="order-card-header">
                <span className="order-card-id">{o.id}</span>
                <span className={`badge badge-${o.status}`}>{o.status}</span>
              </div>
              <div className="order-card-body">
                <span className="order-card-customer">{getUserName(o.userId)}</span>
                <span className="order-card-total">${o.total.toFixed(2)}</span>
              </div>
              <div className="order-card-footer">
                <span>{o.items.length} item(s)</span>
                <span>{o.createdAt}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
