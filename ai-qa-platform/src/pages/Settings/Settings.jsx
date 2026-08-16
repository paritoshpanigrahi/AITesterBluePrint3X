import { useState } from 'react'
import './Settings.css'

export default function Settings() {
  const [theme, setTheme] = useState('light')
  const [notifications, setNotifications] = useState({ email: true, push: false, sms: false })
  const [language, setLanguage] = useState('en')
  const [saved, setSaved] = useState(false)
  const [entriesPerPage, setEntriesPerPage] = useState('20')

  const handleSave = (e) => {
    e.preventDefault()
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="settings-page">
      <div className="page-header"><h1>Settings</h1><p>Customize your application preferences</p></div>

      {saved && <div className="success-message">Settings saved successfully!</div>}

      <form onSubmit={handleSave}>
        <div className="settings-section">
          <h3>Appearance</h3>
          <div className="settings-group">
            <div className="settings-row">
              <span className="settings-label">Theme</span>
              <select value={theme} onChange={e => setTheme(e.target.value)}>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System Default</option>
              </select>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h3>Notifications</h3>
          <div className="settings-group">
            <div className="settings-row">
              <span className="settings-label">Email Notifications</span>
              <label className="toggle"><input type="checkbox" checked={notifications.email} onChange={e => setNotifications(n => ({ ...n, email: e.target.checked }))} /><span className="toggle-slider" /></label>
            </div>
            <div className="settings-row">
              <span className="settings-label">Push Notifications</span>
              <label className="toggle"><input type="checkbox" checked={notifications.push} onChange={e => setNotifications(n => ({ ...n, push: e.target.checked }))} /><span className="toggle-slider" /></label>
            </div>
            <div className="settings-row">
              <span className="settings-label">SMS Notifications</span>
              <label className="toggle"><input type="checkbox" checked={notifications.sms} onChange={e => setNotifications(n => ({ ...n, sms: e.target.checked }))} /><span className="toggle-slider" /></label>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h3>Preferences</h3>
          <div className="settings-group">
            <div className="settings-row">
              <span className="settings-label">Language</span>
              <select value={language} onChange={e => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="ja">Japanese</option>
              </select>
            </div>
            <div className="settings-row">
              <span className="settings-label">Entries per page</span>
              <select value={entriesPerPage} onChange={e => setEntriesPerPage(e.target.value)}>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>
        </div>

        <button type="submit" className="btn btn-primary">Save Settings</button>
      </form>
    </div>
  )
}
