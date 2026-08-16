import { useState } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import { products as initialProducts, categories } from '../../data/mockData'
import './Products.css'

export default function Products() {
  const { isAdmin } = useAuth()
  const [productList, setProductList] = useState(initialProducts)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [showDetail, setShowDetail] = useState(null)
  const [form, setForm] = useState({ name: '', description: '', price: '', category: '', stock: '', status: 'active' })

  const filtered = productList.filter(p => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.description.toLowerCase().includes(search.toLowerCase())
    const matchCategory = !categoryFilter || p.category === categoryFilter
    return matchSearch && matchCategory
  })

  const resetForm = () => setForm({ name: '', description: '', price: '', category: '', stock: '', status: 'active' })

  const openAdd = () => { setEditingProduct(null); resetForm(); setShowModal(true) }

  const openEdit = (p) => {
    setEditingProduct(p)
    setForm({ name: p.name, description: p.description, price: String(p.price), category: p.category, stock: String(p.stock), status: p.status })
    setShowModal(true)
  }

  const handleSave = (e) => {
    e.preventDefault()
    const data = { name: form.name, description: form.description, price: parseFloat(form.price), category: form.category, stock: parseInt(form.stock), status: form.status }
    if (!data.name || !data.price || !data.category) return

    if (editingProduct) {
      setProductList(prev => prev.map(p => p.id === editingProduct.id ? { ...p, ...data, updatedAt: new Date().toISOString().slice(0, 10) } : p))
    } else {
      const newId = Math.max(...productList.map(p => p.id), 0) + 1
      setProductList(prev => [...prev, { id: newId, ...data, image: null, createdAt: new Date().toISOString().slice(0, 10), updatedAt: new Date().toISOString().slice(0, 10) }])
    }
    setShowModal(false)
    resetForm()
  }

  const handleDelete = (id) => {
    if (!isAdmin) return
    if (!confirm('Are you sure you want to delete this product?')) return
    setProductList(prev => prev.filter(p => p.id !== id))
    setShowDetail(null)
  }

  return (
    <div className="products-page">
      <div className="page-header"><h1>Products</h1><p>Manage product catalog</p></div>

      <div className="toolbar">
        <div className="toolbar-left">
          <input className="search-input" type="text" placeholder="Search products..." value={search} onChange={e => setSearch(e.target.value)} />
          <select className="filter-select" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        {isAdmin && <button className="btn btn-primary" onClick={openAdd}>+ Add Product</button>}
      </div>

      {showDetail && (
        <div className="modal-overlay" onClick={() => setShowDetail(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h2>{showDetail.name}</h2><button className="modal-close" onClick={() => setShowDetail(null)}>&times;</button></div>
            <div className="modal-body">
              <p><strong>Category:</strong> {showDetail.category}</p>
              <p><strong>Price:</strong> ${showDetail.price.toFixed(2)}</p>
              <p><strong>Stock:</strong> {showDetail.stock} units</p>
              <p><strong>Status:</strong> <span className={`badge badge-${showDetail.status}`}>{showDetail.status}</span></p>
              <p><strong>Description:</strong> {showDetail.description}</p>
              <p><strong>Created:</strong> {showDetail.createdAt}</p>
              <p><strong>Updated:</strong> {showDetail.updatedAt}</p>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowDetail(null)}>Close</button>
              {isAdmin && <button className="btn btn-primary" onClick={() => { setShowDetail(null); openEdit(showDetail) }}>Edit</button>}
              {isAdmin && <button className="btn btn-danger" onClick={() => handleDelete(showDetail.id)}>Delete</button>}
            </div>
          </div>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => { setShowModal(false); resetForm() }}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header"><h2>{editingProduct ? 'Edit Product' : 'Add Product'}</h2><button className="modal-close" onClick={() => { setShowModal(false); resetForm() }}>&times;</button></div>
            <form onSubmit={handleSave}>
              <div className="modal-body">
                <div className="form-group"><label>Name</label><input type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required /></div>
                <div className="form-group"><label>Description</label><textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={3} /></div>
                <div className="form-row">
                  <div className="form-group"><label>Price ($)</label><input type="number" step="0.01" min="0" value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} required /></div>
                  <div className="form-group"><label>Stock</label><input type="number" min="0" value={form.stock} onChange={e => setForm(f => ({ ...f, stock: e.target.value }))} /></div>
                </div>
                <div className="form-row">
                  <div className="form-group"><label>Category</label><select value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} required><option value="">Select...</option>{categories.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
                  <div className="form-group"><label>Status</label><select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}><option value="active">Active</option><option value="inactive">Inactive</option></select></div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => { setShowModal(false); resetForm() }}>Cancel</button>
                <button type="submit" className="btn btn-primary">{editingProduct ? 'Update' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="products-grid">
        {filtered.length === 0 ? <p className="empty-text">No products found</p> : (
          filtered.map(p => (
            <div key={p.id} className="product-card" onClick={() => setShowDetail(p)}>
              <div className="product-header">
                <span className={`badge badge-${p.status}`}>{p.status}</span>
                <span className="product-category">{p.category}</span>
              </div>
              <h3 className="product-name">{p.name}</h3>
              <p className="product-desc">{p.description.slice(0, 80)}{p.description.length > 80 ? '...' : ''}</p>
              <div className="product-footer">
                <span className="product-price">${p.price.toFixed(2)}</span>
                <span className="product-stock">Stock: {p.stock}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
