import React, { useState, useEffect, useCallback, useRef } from 'react';
import * as api from './api';
import './App.css';

const PROVIDERS = {
  openai: { label: 'OpenAI', models: ['gpt-4o', 'gpt-4o-mini', 'o3-mini', 'o4-mini'] },
  anthropic: { label: 'Anthropic Claude', models: ['claude-sonnet-4-5', 'claude-3-7-sonnet', 'claude-opus-4'] },
  google: { label: 'Google Gemini', models: ['gemini-2.0-flash', 'gemini-2.5-pro'] },
  groq: { label: 'Groq', models: ['llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'llama-4-maverick-17b-128e-instruct', 'llama-4-scout-instruct', 'gpt-oss-120b', 'gpt-oss-20b', 'gpt-oss-safeguard-20b', 'groq/compound', 'groq/compound-mini', 'whisper-large-v3', 'whisper-large-v3-turbo', 'meta-llama/llama-guard-4-12b', 'moonshotai/kimi-k2-instruct'] },
  opencode: { label: 'OpenCode Zen', models: ['big-pickle', 'deepseek-v4-flash-free', 'deepseek-v4-flash', 'kimi-k3', 'glm-5.2', 'qwen3.7-max', 'minimax-m3'] },
  ollama: { label: 'Ollama (Local)', models: ['llama3', 'mistral:7b-v0.3', 'phi3:mini', 'gemma2:9b', 'codellama:13b', 'qwen2.5:7b', 'vicuna:13b', 'openhermes:2.5'] },
  'github-copilot': { label: 'VS Code GitHub Copilot', models: ['gpt-4o', 'claude-sonnet-4-5', 'gemini-2.0-flash-001'] },
};

export default function App() {
  const [activeTab, setActiveTab] = useState('automation');
  const [activeAutomationSubTab, setActiveAutomationSubTab] = useState('fresh');
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    llmProvider: 'openai', llmModel: 'gpt-4o', openaiApiKey: '',
    anthropicApiKey: '', googleApiKey: '', groqApiKey: '', githubCopilotToken: '', ollamaBaseUrl: 'http://localhost:11434',
    opencodeApiKey: '',
    outputDir: '', theme: 'dark',
    jiraUrl: '', jiraEmail: '', jiraApiToken: '',
    confluenceUrl: '', confluenceEmail: '', confluenceApiToken: '',
    llmMaxTokens: 4096,
    customModels: {},
  });
  const [appVersion, setAppVersion] = useState('1.0.0');
  const [platform, setPlatform] = useState('windows');
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [error, setError] = useState('');
  const [showManual, setShowManual] = useState(false);
  const [backendReady, setBackendReady] = useState(false);

  useEffect(() => {
    initApp();
  }, []);

  useEffect(() => {
    window.electronAPI?.onOpenSettings(() => setShowSettings(true));
    window.electronAPI?.onOpenManual(() => setShowManual(true));
  }, []);

  async function initApp() {
    try {
      const s = await window.electronAPI?.getSettings();
      if (s) setSettings(prev => ({ ...prev, ...s }));
      const v = await window.electronAPI?.getVersion();
      if (v) setAppVersion(v);
      if (window.electronAPI?.platform) setPlatform(window.electronAPI.platform);
    } catch (e) { console.error('Failed to load settings:', e); }
    try {
      const cfg = await api.getConfig();
      if (cfg.output_dir) {
        setSettings(prev => ({ ...prev, outputDir: cfg.output_dir }));
      }
    } catch (e) {
      console.error('Failed to load backend config:', e);
    }
    pollBackend();
  }

  async function pollBackend() {
    for (let i = 0; i < 120; i++) {
      try {
        const h = await api.getHealth();
        if (h.status === 'ok') {
          setBackendReady(true);
          setStatusMessage('Backend ready');
          return;
        }
      } catch (e) { /* still starting */ }
      await new Promise(r => setTimeout(r, 500));
    }
    setError('Failed to connect to backend after 60 seconds');
  }

  async function handleSaveSettings(newSettings) {
    const merged = { ...settings, ...newSettings };
    setSettings(merged);
      await window.electronAPI?.saveSettings(merged);
    if (merged.outputDir) {
      try {
        await api.updateConfig(merged.outputDir);
      } catch (e) {
        console.error('Failed to sync output dir to backend:', e);
      }
    }
  }

  async function handleRestartBackend() {
    setStatusMessage('Restarting AI engine...');
    setError('');
    await window.electronAPI?.restartBackend();
    await pollBackend();
    setStatusMessage('AI engine restarted');
  }

  if (!backendReady) {
    return (
      <div className="splash-screen">
        <div className="spinner"></div>
        <h2>Starting AI engine...</h2>
        <p>Initializing backend services</p>
        {error && <p className="error-text">{error}</p>}
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-title">
          <h1>AI QA Platform</h1>
          <span className="version-badge">v{appVersion}</span>
        </div>
        <nav className="tab-nav">
          {[
            { id: 'automation', label: 'Automation Tests' },
            { id: 'manual', label: 'Manual Tests' },
          ].map(tab => (
            <button
              key={tab.id}
              className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
        <button className="settings-btn" onClick={() => setShowManual(true)} title="User Manual (F1)">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 3h12v14H4zM4 7h12M7 3v4"/>
            <circle cx="10" cy="11" r="1"/><path d="M10 12v2"/>
          </svg>
        </button>
        <button className="settings-btn" onClick={() => setShowSettings(true)} title="Settings">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="10" cy="10" r="3"/>
            <path d="M10 1v2M10 17v2M1 10h2M17 10h2M3.93 3.93l1.41 1.41M14.66 14.66l1.41 1.41M3.93 16.07l1.41-1.41M14.66 5.34l1.41-1.41"/>
          </svg>
        </button>
      </header>

      <div className="app-content">
        <div className="main-panel">
          {statusMessage && <div className="status-bar">{statusMessage}</div>}
          {error && <div className="error-bar">{error}</div>}

          {activeTab === 'automation' && <AutomationTestsTab activeSubTab={activeAutomationSubTab} onSubTabChange={setActiveAutomationSubTab} outputDir={settings.outputDir} settings={settings} />}
          {activeTab === 'manual' && <ManualTestsTab settings={settings} />}
        </div>
      </div>

      {showSettings && (
        <SettingsPanel
          settings={settings}
          onSave={handleSaveSettings}
          onRestart={handleRestartBackend}
          onClose={() => setShowSettings(false)}
          appVersion={appVersion}
          platform={platform}
          onOpenManual={() => setShowManual(true)}
        />
      )}

      {showManual && <UserManualPanel onClose={() => setShowManual(false)} outputDir={settings.outputDir} />}
    </div>
  );
}

function FolderPickerModal({ title, initialPath, onSelect, onClose }) {
  const [currentPath, setCurrentPath] = useState(initialPath || '');
  const [entries, setEntries] = useState([]);
  const [parent, setParent] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function load(path) {
    setLoading(true);
    setError('');
    try {
      const res = await api.browseDirectories(path);
      setCurrentPath(res.path || '');
      setEntries(res.entries || []);
      setParent(res.parent || null);
      if (res.error) setError(res.error);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  useEffect(() => {
    load(initialPath);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialPath]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal folder-picker" onClick={e => e.stopPropagation()} style={{ maxWidth: 560 }}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <div className="folder-picker-path">
            <span className="folder-picker-label">Current path:</span>
            <span className="path-resolve">{currentPath || '(select a drive / enter a path)'}</span>
          </div>
          {error && <div className="error-bar">{error}</div>}
          <div className="folder-picker-actions">
            <button className="btn btn-secondary" onClick={() => load('')} disabled={loading} title="Go to drives (or home)">
              Drives / Home
            </button>
            <button className="btn btn-secondary" onClick={() => load(parent)} disabled={!parent || loading} title="Go up one level">
              Up
            </button>
            <input
              type="text"
              value={currentPath}
              onChange={e => setCurrentPath(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') load(currentPath); }}
              placeholder="Type a full path and press Enter"
            />
          </div>
          <div className="folder-picker-list">
            {entries.map(entry => (
              <button
                key={entry.path}
                className="folder-picker-item"
                onClick={() => load(entry.path)}
                title={entry.path}
              >
                <span className="folder-picker-icon">&#128193;</span>
                <span className="folder-picker-name">{entry.name}</span>
                <span className="folder-picker-fullpath">{entry.path}</span>
              </button>
            ))}
            {!loading && entries.length === 0 && <p className="text-muted">No subfolders found</p>}
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={() => onSelect(currentPath)} disabled={!currentPath}>
            Select This Folder
          </button>
        </div>
      </div>
    </div>
  );
}

function SettingsPanel({ settings, onSave, onRestart, onClose, appVersion, platform, onOpenManual }) {
  const [local, setLocal] = useState({ ...settings });
  const [saving, setSaving] = useState(false);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [ollamaLoading, setOllamaLoading] = useState(false);
  const [ollamaError, setOllamaError] = useState('');
  const [showFolderPicker, setShowFolderPicker] = useState(false);
  const outputDirInputRef = useRef(null);

  const provider = local.llmProvider;

  function update(key, value) {
    setLocal(prev => ({ ...prev, [key]: value }));
  }

  function getApiKeyField() {
    switch (provider) {
      case 'anthropic': return 'anthropicApiKey';
      case 'google': return 'googleApiKey';
      case 'groq': return 'groqApiKey';
      case 'opencode': return 'opencodeApiKey';
      default: return 'openaiApiKey';
    }
  }

  function getApiKeyValue() {
    switch (provider) {
      case 'anthropic': return local.anthropicApiKey;
      case 'google': return local.googleApiKey;
      case 'groq': return local.groqApiKey;
      case 'opencode': return local.opencodeApiKey;
      default: return local.openaiApiKey;
    }
  }

  function needsApiKey() {
    return provider !== 'ollama' && provider !== 'github-copilot';
  }

  function getModelList() {
    const defaults = PROVIDERS[provider]?.models || [];
    const custom = (local.customModels?.[provider] || []);
    const ollama = provider === 'ollama' ? ollamaModels : [];
    const combined = [...new Set([...defaults, ...ollama, ...custom])];
    return combined;
  }

  async function handleFetchOllamaModels() {
    if (!local.ollamaBaseUrl) return;
    setOllamaLoading(true);
    setOllamaError('');
    try {
      const base = local.ollamaBaseUrl.replace(/\/+$/, '');
      const res = await fetch(`${base}/api/tags`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const names = (data.models || []).map(m => m.name);
      setOllamaModels(names);
    } catch (e) {
      setOllamaError('Failed to fetch models: ' + e.message);
    }
    setOllamaLoading(false);
  }

  useEffect(() => {
    if (provider === 'ollama') {
      handleFetchOllamaModels();
    }
  }, [provider, local.ollamaBaseUrl]);

  async function handleSave() {
    const custom = local.customModels || {};
    const current = local.llmModel;
    const defaults = PROVIDERS[provider]?.models || [];
    const ollama = provider === 'ollama' ? ollamaModels : [];
    const known = [...defaults, ...ollama];
    if (current && !known.includes(current) && !(custom[provider] || []).includes(current)) {
      custom[provider] = [...(custom[provider] || []), current];
    }
    setSaving(true);
    await onSave({ ...local, customModels: custom });
    setSaving(false);
    onClose();
  }

  function handleBrowse() {
    if (window.electronAPI?.selectFolder) {
      window.electronAPI.selectFolder().then(folder => {
        if (folder) update('outputDir', folder);
      });
    } else {
      setShowFolderPicker(true);
    }
  }

  function handleDirFileSelected(e) {
    e.target.value = '';
    setShowFolderPicker(true);
  }

  async function handleOpenFolder() {
    if (local.outputDir) {
      await window.electronAPI?.openPath(local.outputDir);
    }
  }

  const platformName = { win32: 'Windows', darwin: 'macOS', linux: 'Linux' }[platform] || platform;
  const modelList = getModelList();

  return (
    <>
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal settings-panel" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Settings</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <section className="settings-section">
            <h3>AI Provider</h3>
            <div className="form-group">
              <label>Provider</label>
              <select value={provider} onChange={e => {
                update('llmProvider', e.target.value);
                const p = PROVIDERS[e.target.value];
                if (p && p.models.length > 0) update('llmModel', p.models[0]);
              }}>
                {Object.entries(PROVIDERS).map(([k, v]) => (
                  <option key={k} value={k}>{v.label}</option>
                ))}
              </select>
            </div>

            {provider === 'github-copilot' && (
              <div className="form-group" style={{ marginBottom: 8 }}>
                <p className="text-muted" style={{ fontSize: 12, lineHeight: 1.4 }}>
                  Uses your VS Code GitHub Copilot subscription. The GitHub token is auto-detected from the <code>GITHUB_TOKEN</code> environment variable or the <code>gh</code> CLI. No API key required.
                </p>
              </div>
            )}
            <div className="form-group">
              <label>Model</label>
              <select value={local.llmModel} onChange={e => update('llmModel', e.target.value)} style={{ width: '100%' }}>
                {modelList.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            {provider === 'ollama' ? (
              <div className="form-group">
                <label>Base URL</label>
                <input type="text" value={local.ollamaBaseUrl} onChange={e => update('ollamaBaseUrl', e.target.value)} placeholder="http://localhost:11434" />
                {ollamaLoading && <p className="text-muted" style={{ fontSize: 11, marginTop: 2 }}>Loading models...</p>}
                {ollamaError && <p className="error-text" style={{ fontSize: 11, marginTop: 2 }}>{ollamaError}</p>}
              </div>
            ) : provider === 'github-copilot' ? (
              <div className="form-group">
                <label>GitHub Token <span className="text-muted" style={{ fontWeight: 400 }}>(optional)</span></label>
                <input
                  type="password"
                  value={local.githubCopilotToken || ''}
                  onChange={e => update('githubCopilotToken', e.target.value)}
                  placeholder="Leave blank to auto-detect from GITHUB_TOKEN env or gh CLI"
                />
              </div>
            ) : needsApiKey() && (
              <div className="form-group">
                <label>API Key</label>
                <input
                  type="password"
                  value={getApiKeyValue()}
                  onChange={e => update(getApiKeyField(), e.target.value)}
                  placeholder={`Enter ${PROVIDERS[provider]?.label} API key`}
                />
              </div>
            )}
            <p className="text-muted" style={{ fontSize: 11, marginTop: 4 }}>Select a model. Custom models typed in the past are also listed.</p>
            <div className="form-group" style={{ marginTop: 16 }}>
              <label>Max Output Tokens per LLM Call: <strong>{local.llmMaxTokens || 4096}</strong></label>
              <input type="range" min="512" max="16384" step="512"
                value={local.llmMaxTokens || 4096}
                onChange={e => update('llmMaxTokens', parseInt(e.target.value, 10))}
                style={{ width: '100%' }}
              />
              <p className="text-muted" style={{ fontSize: 11, marginTop: 2 }}>
                Lower values (e.g., 2048) reduce token usage to stay within provider rate limits.
              </p>
            </div>
            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save & Apply'}
            </button>
          </section>

          <section className="settings-section">
            <h3>Test Output Directory</h3>
            <div className="form-group">
              <label>Output Path</label>
              <div className="input-with-btn">
                <input type="text" value={local.outputDir} onChange={e => update('outputDir', e.target.value)} />
                <button className="btn btn-secondary" onClick={handleBrowse}>Browse</button>
              </div>
              <input
                type="file"
                ref={outputDirInputRef}
                onChange={handleDirFileSelected}
                webkitdirectory=""
                directory=""
                style={{ display: 'none' }}
              />
              {local.outputDir && <p className="path-resolve">{local.outputDir}</p>}
              <button className="btn btn-secondary" onClick={handleOpenFolder} style={{ marginTop: 8 }}>
                Open in Explorer
              </button>
            </div>
          </section>

          <section className="settings-section">
            <h3>Atlassian Integration</h3>
            <p className="text-muted" style={{ fontSize: 12, marginBottom: 8 }}>Enter credentials for Jira and Confluence to fetch ticket and page content as test context.</p>
            <div className="form-group">
              <label>Jira URL</label>
              <input type="text" value={local.jiraUrl || ''} onChange={e => update('jiraUrl', e.target.value)} placeholder="https://your-domain.atlassian.net" />
            </div>
            <div className="form-group">
              <label>Jira Email</label>
              <input type="text" value={local.jiraEmail || ''} onChange={e => update('jiraEmail', e.target.value)} placeholder="email@example.com" />
            </div>
            <div className="form-group">
              <label>Jira API Token</label>
              <input type="password" value={local.jiraApiToken || ''} onChange={e => update('jiraApiToken', e.target.value)} placeholder="Atlassian API token or PAT" />
            </div>
            <div className="form-group">
              <label>Confluence URL</label>
              <input type="text" value={local.confluenceUrl || ''} onChange={e => update('confluenceUrl', e.target.value)} placeholder="https://your-domain.atlassian.net/wiki" />
            </div>
            <div className="form-group">
              <label>Confluence Email</label>
              <input type="text" value={local.confluenceEmail || ''} onChange={e => update('confluenceEmail', e.target.value)} placeholder="email@example.com" />
            </div>
            <div className="form-group">
              <label>Confluence API Token</label>
              <input type="password" value={local.confluenceApiToken || ''} onChange={e => update('confluenceApiToken', e.target.value)} placeholder="Atlassian API token or PAT" />
            </div>
            <p className="text-muted" style={{ fontSize: 11, marginTop: 2 }}>Get an API token at https://id.atlassian.com/manage/api-tokens. Leave email blank and paste a PAT to use Bearer auth. Restart AI Engine after saving.</p>
          </section>

          <section className="settings-section">
            <h3>Application</h3>
            <button className="btn btn-warning" onClick={onRestart}>Restart AI Engine</button>
            <div className="info-row"><span>Version:</span><span>{appVersion}</span></div>
            <div className="info-row"><span>Platform:</span><span>{platformName}</span></div>
          </section>

          <section className="settings-section">
            <h3>About</h3>
            <p>AI QA Platform v{appVersion}</p>
            <p className="text-muted">Automated test generation and execution platform powered by AI.</p>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button className="btn btn-secondary" onClick={onOpenManual}>User Manual</button>
              <button className="btn btn-secondary" onClick={() => {
                window.electronAPI?.openExternal('https://github.com/anomalyco/opencode');
              }}>GitHub Repository</button>
            </div>
          </section>
        </div>
      </div>
    </div>

      {showFolderPicker && (
        <FolderPickerModal
          title="Select Output Folder"
          initialPath={local.outputDir || ''}
          onSelect={path => { if (path && path.trim()) update('outputDir', path.trim()); setShowFolderPicker(false); }}
          onClose={() => setShowFolderPicker(false)}
        />
      )}
    </>
  );
}

function AutomationTestsTab({ activeSubTab, onSubTabChange, outputDir, settings }) {
  return (
    <div className="automation-tests-tab">
      <div className="sub-tabs">
        {[
          { id: 'fresh', label: 'Fresh Generate' },
          { id: 'add', label: 'Add Feature' },
          { id: 'modify', label: 'Modify Tests' },
          { id: 'registry', label: 'Test Registry' },
        ].map(tab => (
          <button key={tab.id} className={`tab-btn ${activeSubTab === tab.id ? 'active' : ''}`} onClick={() => onSubTabChange(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>
      {activeSubTab === 'fresh' && <GenerateForm mode="fresh" title="Fresh Generate" outputDir={outputDir} settings={settings} />}
      {activeSubTab === 'add' && <GenerateForm mode="add" title="Add Feature" requiresFeatureName outputDir={outputDir} settings={settings} />}
      {activeSubTab === 'modify' && <GenerateForm mode="modify" title="Modify Tests" requiresTestFileName outputDir={outputDir} settings={settings} />}
      {activeSubTab === 'registry' && <RegistryTab />}
    </div>
  );
}

function GenerateForm({ mode, title, requiresFeatureName, requiresTestFileName, outputDir, settings }) {
  const [form, setForm] = useState({
    url: '', requirement: '', featureName: '', testFileName: '',
    prdFile: null, manualTestsFile: null, openapiFile: null, envFile: null,
    confluenceUrl: '', jiraTicketId: '', jiraSprintId: '', jiraProjectKey: '',
    codebasePath: '',
  });
  const [contextResult, setContextResult] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [contextLoading, setContextLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeResultTab, setActiveResultTab] = useState('locators');
  const [showResolveDialog, setShowResolveDialog] = useState(false);
  const [pendingActions, setPendingActions] = useState([]);
  const [lastPayload, setLastPayload] = useState(null);
  const [showSetupDialog, setShowSetupDialog] = useState(false);
  const [setupInfo, setSetupInfo] = useState(null);
  const [setupRunning, setSetupRunning] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [llmErrors, setLlmErrors] = useState([]);
  const [showCodebasePicker, setShowCodebasePicker] = useState(false);
  const codebaseInputRef = useRef(null);

  const statusSteps = [
    'Crawling page with Playwright...',
    'Generating locators via AI...',
    'Planning test scenarios...',
    'Writing test files...',
  ];

  useEffect(() => {
    if (!loading) { setStatusMsg(''); return; }
    let i = 0;
    setStatusMsg(statusSteps[0]);
    const t = setInterval(() => {
      i++;
      if (i < statusSteps.length) setStatusMsg(statusSteps[i]);
    }, 6000);
    return () => clearInterval(t);
  }, [loading]);

  function update(key, value) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  function handleBrowseCodebase() {
    if (window.electronAPI?.selectFolder) {
      window.electronAPI.selectFolder().then(folder => {
        if (folder) update('codebasePath', folder);
      });
    } else {
      setShowCodebasePicker(true);
    }
  }

  function handleCodebaseFileSelected(e) {
    e.target.value = '';
    setShowCodebasePicker(true);
  }

  const pendingActionRef = useRef(null);

  async function requireSetup(action) {
    try {
      const info = await api.checkSetup();
      if (!info.playwright_installed) {
        setSetupInfo(info);
        pendingActionRef.current = action;
        setShowSetupDialog(true);
        return true;
      }
    } catch (e) { /* ignore, proceed anyway */ }
    return false;
  }

  async function handleConfirmSetup() {
    setSetupRunning(true);
    setShowSetupDialog(false);
    try {
      await api.setupPlaywright();
      const next = pendingActionRef.current;
      pendingActionRef.current = null;
      if (next) await next();
    } catch (e) {
      setError('Setup failed: ' + e.message);
    }
    setSetupRunning(false);
  }

  async function handlePreview() {
    setContextLoading(true);
    setError('');
    setContextResult(null);
    try {
      const payload = buildPayload();
      const res = await api.ingestContext(payload);
      setContextResult(res);
    } catch (e) {
      setError(e.message);
    }
    setContextLoading(false);
  }

  async function handleGenerate() {
    if (!form.url && mode === 'fresh') {
      setError('Please enter an Application URL to generate locators.');
      return;
    }
    const doGenerate = async () => {
      setLoading(true);
      setError('');
      setResult(null);
      setLlmErrors([]);
      try {
        const payload = buildPayload();
        setLastPayload(payload);
        let res;
        if (mode === 'add') {
          payload.feature_name = form.featureName;
          res = await api.addFeature(payload);
        } else if (mode === 'modify') {
          payload.test_file_name = form.testFileName;
          res = await api.modifyTests(payload);
        } else {
          res = await api.generateTests(payload);
        }
        setResult(res);
        if (res.llm_errors?.length > 0) setLlmErrors(res.llm_errors);
        if (res.duplicate_result?.has_duplicates && res.duplicate_result?.pending_actions?.length > 0) {
          const actions = res.duplicate_result.pending_actions.map(a => ({ ...a }));
          setPendingActions(actions);
          setShowResolveDialog(true);
        }
      } catch (e) {
        setError(e.message);
      }
      setLoading(false);
    };

    const needsSetup = await requireSetup(doGenerate);
    if (needsSetup) return;
    await doGenerate();
  }

  async function handleApplyResolutions() {
    if (!lastPayload) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const payload = { ...lastPayload };
      payload.scenario_actions = pendingActions.map(a => ({
        name: a.scenario_name,
        existing_name: a.existing_name,
        action: a.action,
      }));
      let res;
      if (mode === 'add') {
        payload.feature_name = form.featureName;
        res = await api.addFeature(payload);
      } else if (mode === 'modify') {
        payload.test_file_name = form.testFileName;
        res = await api.modifyTests(payload);
      } else {
        res = await api.generateTests(payload);
      }
      setResult(res);
      setShowResolveDialog(false);
      setPendingActions([]);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  function updateAction(index, newAction) {
    setPendingActions(prev => {
      const next = [...prev];
      next[index] = { ...next[index], action: newAction };
      return next;
    });
  }

  async function handlePreviewPlan() {
    const doPreview = async () => {
      setLoading(true);
      setError('');
      setResult(null);
      try {
        const payload = buildPayload();
        const res = await api.previewPlan(payload);
        setResult(res);
      } catch (e) {
        setError(e.message);
      }
      setLoading(false);
    };

    const needsSetup = await requireSetup(doPreview);
    if (needsSetup) return;
    await doPreview();
  }

  function getLlmApiKey() {
    switch (settings.llmProvider) {
      case 'anthropic': return settings.anthropicApiKey;
      case 'google': return settings.googleApiKey;
      case 'groq': return settings.groqApiKey;
      case 'opencode': return settings.opencodeApiKey;
      default: return settings.openaiApiKey;
    }
  }

  function buildPayload() {
    return {
      url: form.url || undefined,
      requirement: form.requirement || undefined,
      confluence_url: form.confluenceUrl || undefined,
      jira_ticket_id: form.jiraTicketId || undefined,
      jira_sprint_id: form.jiraSprintId || undefined,
      jira_project_key: form.jiraProjectKey || undefined,
      openapi_path: form.openapiFile?.name || undefined,
      env_file_path: form.envFile?.name || undefined,
      codebase_path: form.codebasePath || undefined,
      output_dir: outputDir || undefined,
      llm_provider: settings.llmProvider || undefined,
      llm_model: settings.llmModel || undefined,
      llm_api_key: getLlmApiKey() || undefined,
      llm_max_tokens: settings.llmMaxTokens || undefined,
    };
  }

  return (
    <div className="generate-form">
      <h2>{title}</h2>

      <div className="form-grid">
        <div className="form-group">
          <label>Application URL (Mandatory)</label>
          <input type="text" value={form.url} onChange={e => update('url', e.target.value)} placeholder="https://example.com" />
        </div>

        <div className="form-group">
          <label>Codebase Path</label>
          <div className="input-with-btn">
            <input type="text" value={form.codebasePath} onChange={e => update('codebasePath', e.target.value)} placeholder="C:\project" />
            <button className="btn btn-secondary" onClick={handleBrowseCodebase}>Browse</button>
          </div>
          <input
            type="file"
            ref={codebaseInputRef}
            onChange={handleCodebaseFileSelected}
            webkitdirectory=""
            directory=""
            style={{ display: 'none' }}
          />
        </div>

        {requiresFeatureName && (
          <div className="form-group">
            <label>Feature Name *</label>
            <input type="text" value={form.featureName} onChange={e => update('featureName', e.target.value)} placeholder="e.g., User Authentication" required />
          </div>
        )}

        {requiresTestFileName && (
          <div className="form-group">
            <label>Test File to Modify *</label>
            <input type="text" value={form.testFileName} onChange={e => update('testFileName', e.target.value)} placeholder="e.g., auth.spec.ts" required />
          </div>
        )}

        <div className="form-group full-width">
          <label>Requirement / Steps</label>
          <textarea
            value={form.requirement}
            onChange={e => update('requirement', e.target.value)}
            rows={6}
            placeholder="Paste requirements, user stories, or test steps here...&#10;&#10;Examples:&#10;• Raw steps: 1. Navigate to login page | 2. Enter email | 3. Click Sign In&#10;• User story: As a user, I want to log in so that I can access my dashboard&#10;• Requirements: The login page should have email, password fields and a Sign In button"
          />
          <p className="text-muted" style={{ fontSize: 11, marginTop: 4 }}>
            The AI will automatically detect whether you pasted raw test steps (preserved verbatim) or requirements (converted to scenarios).
          </p>
        </div>

        <div className="form-group">
          <label>PRD File</label>
          <input type="file" onChange={e => update('prdFile', e.target.files[0])} accept=".pdf,.docx,.txt,.md,.xlsx,.csv" />
        </div>

        <div className="form-group">
          <label>Manual Test Cases</label>
          <input type="file" onChange={e => update('manualTestsFile', e.target.files[0])} accept=".xlsx,.csv" />
        </div>

        <div className="form-group">
          <label>OpenAPI Spec</label>
          <input type="file" onChange={e => update('openapiFile', e.target.files[0])} accept=".yaml,.json" />
        </div>

        <div className="form-group">
          <label>.env File</label>
          <input type="file" onChange={e => update('envFile', e.target.files[0])} accept=".env" />
        </div>

        <div className="form-group">
          <label>Confluence URL</label>
          <input type="text" value={form.confluenceUrl} onChange={e => update('confluenceUrl', e.target.value)} placeholder="https://confluence.company.com/..." />
        </div>

        <div className="form-group">
          <label>Jira Ticket ID</label>
          <input type="text" value={form.jiraTicketId} onChange={e => update('jiraTicketId', e.target.value)} placeholder="PROJ-123" autoComplete="off" />
        </div>

        <div className="form-group">
          <label>Jira Sprint ID</label>
          <input type="text" value={form.jiraSprintId} onChange={e => update('jiraSprintId', e.target.value)} placeholder="123" />
        </div>

        <div className="form-group">
          <label>Jira Project Key</label>
          <input type="text" value={form.jiraProjectKey} onChange={e => update('jiraProjectKey', e.target.value)} placeholder="PROJ" />
        </div>

        <div className="form-group">
          <label>Output Path</label>
          <div className="input-with-btn">
            <input type="text" value={outputDir || ''} readOnly placeholder="Not configured" />
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button className="btn btn-secondary" onClick={handlePreview} disabled={contextLoading}>
          {contextLoading ? 'Analyzing...' : 'Preview Context'}
        </button>
        <button className="btn btn-secondary" onClick={handlePreviewPlan} disabled={loading}>
          {loading ? statusMsg || 'Planning...' : 'Preview Plan'}
        </button>
        <button className="btn btn-primary" onClick={handleGenerate} disabled={loading || setupRunning}>
          {setupRunning ? 'Setting up Playwright...' : loading ? statusMsg || 'Generating...' : mode === 'fresh' ? 'Fresh Generate' : mode === 'add' ? 'Add Feature' : 'Modify Tests'}
        </button>
      </div>

      {showSetupDialog && setupInfo && (
        <div className="modal-overlay" onClick={() => setShowSetupDialog(false)}>
          <div className="modal setup-dialog" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>First-Time Setup Required</h2>
              <button className="close-btn" onClick={() => setShowSetupDialog(false)}>&times;</button>
            </div>
            <div className="modal-body">
              <p>This is the first time generating tests. Playwright needs to be set up at the output directory:</p>
              <p className="path-resolve" style={{ fontSize: 13, marginTop: 8 }}>{setupInfo.output_dir}</p>
              <ul style={{ marginTop: 12, fontSize: 13, lineHeight: 1.8 }}>
                {!setupInfo.npm_found && <li className="text-muted">&#10003; Node.js / npm found</li>}
                <li className={setupInfo.npm_found ? 'text-muted' : ''}>
                  {setupInfo.npm_found ? '&#10003;' : '&#10007;'} npm available
                </li>
                <li className={setupInfo.playwright_installed ? 'text-muted' : ''}>
                  {setupInfo.playwright_installed ? '&#10003;' : '&#10007;'} Playwright project initialized
                </li>
              </ul>
              <p className="text-muted" style={{ marginTop: 8, fontSize: 12 }}>
                This will run <code>npm init</code> and install Playwright with Chromium browser (~200 MB download).
              </p>
            </div>
            <div className="modal-footer" style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button className="btn btn-secondary" onClick={() => setShowSetupDialog(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleConfirmSetup}>Confirm &amp; Generate</button>
            </div>
          </div>
        </div>
      )}

      {error && <div className="error-bar">{error}</div>}

      {contextResult && (
        <div className="context-preview">
          <h3>Context Preview</h3>
          <div className="context-grid">
            <div className="context-item"><span className="context-label">Sources:</span> {contextResult.sources_loaded?.join(', ') || 'None'}</div>
            <div className="context-item"><span className="context-label">Routes Found:</span> {contextResult.routes_found}</div>
            <div className="context-item"><span className="context-label">Elements Found:</span> {contextResult.elements_found}</div>
            <div className="context-item"><span className="context-label">API Endpoints:</span> {contextResult.api_endpoints_found}</div>
            <div className="context-item"><span className="context-label">Resolved URL:</span> {contextResult.resolved_url || 'N/A'}</div>
            <div className="context-item"><span className="context-label">Infer Mode:</span> {contextResult.infer_mode}</div>
            <div className="context-item full-width"><span className="context-label">Requirement Preview:</span><p>{contextResult.requirement_preview || 'N/A'}</p></div>
          </div>
        </div>
      )}

      {result && <ResultPanel result={result} activeTab={activeResultTab} onTabChange={setActiveResultTab} outputDir={outputDir} />}

      {llmErrors.length > 0 && (
        <div className="modal-overlay" onClick={() => setLlmErrors([])}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h2 style={{ color: '#f59e0b' }}>AI Provider Issues</h2>
              <button className="close-btn" onClick={() => setLlmErrors([])}>&times;</button>
            </div>
            <div className="modal-body" style={{ maxHeight: 400, overflowY: 'auto' }}>
              {(() => {
                const groups = {};
                llmErrors.forEach(err => {
                  const key = err.type + '::' + (err.suggestion || '');
                  if (!groups[key]) groups[key] = { ...err, count: 0 };
                  groups[key].count++;
                });
                const grouped = Object.values(groups);
                return grouped.map((err, i) => (
                  <div key={i} style={{ marginBottom: i < grouped.length - 1 ? 16 : 0, paddingBottom: i < grouped.length - 1 ? 16 : 0, borderBottom: i < grouped.length - 1 ? '1px solid var(--border)' : 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{
                        display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, textTransform: 'uppercase',
                        background: err.type === 'auth_error' ? '#ef4444' : err.type === 'rate_limit' ? '#f59e0b' : err.type === 'model_not_found' ? '#8b5cf6' : err.type === 'timeout' ? '#3b82f6' : '#6b7280',
                        color: '#fff',
                      }}>{err.type}{err.count > 1 ? ` (×${err.count})` : ''}</span>
                    </div>
                    <p style={{ margin: 0, fontSize: 13, color: 'var(--text-primary)' }}>{err.message}</p>
                    <p style={{ margin: '6px 0 0 0', fontSize: 12, color: 'var(--text-muted)' }}><strong>Suggestion:</strong> {err.suggestion}</p>
                  </div>
                ));
              })()}
            </div>
            <div className="modal-footer" style={{ padding: '12px 20px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary" onClick={() => setLlmErrors([])}>Dismiss</button>
            </div>
          </div>
        </div>
      )}

      {showResolveDialog && pendingActions.length > 0 && (
        <div className="resolve-overlay" onClick={() => setShowResolveDialog(false)}>
          <div className="resolve-dialog" onClick={e => e.stopPropagation()}>
            <div className="resolve-header">
              <h3>Duplicate Scenarios Found</h3>
              <p className="text-muted">Choose how to handle each duplicate:</p>
            </div>
            <div className="resolve-list">
              {pendingActions.map((item, i) => (
                <div key={i} className="resolve-item">
                  <div className="resolve-item-info">
                    <span className="resolve-new"><strong>New:</strong> {item.scenario_name}</span>
                    <span className="resolve-existing"><strong>Existing:</strong> {item.existing_name}</span>
                    <span className="resolve-sim">Similarity: {(item.name_similarity * 100).toFixed(0)}%</span>
                  </div>
                  <div className="resolve-options">
                    <label className={`resolve-option ${item.action === 'skip' ? 'selected' : ''}`}>
                      <input type="radio" name={`action-${i}`} value="skip" checked={item.action === 'skip'} onChange={() => updateAction(i, 'skip')} />
                      <span>Skip (keep existing)</span>
                    </label>
                    <label className={`resolve-option ${item.action === 'override' ? 'selected' : ''}`}>
                      <input type="radio" name={`action-${i}`} value="override" checked={item.action === 'override'} onChange={() => updateAction(i, 'override')} />
                      <span>Override (replace)</span>
                    </label>
                    <label className={`resolve-option ${item.action === 'remove' ? 'selected' : ''}`}>
                      <input type="radio" name={`action-${i}`} value="remove" checked={item.action === 'remove'} onChange={() => updateAction(i, 'remove')} />
                      <span>Remove (delete existing)</span>
                    </label>
                  </div>
                </div>
              ))}
            </div>
            <div className="resolve-footer">
              <button className="btn btn-secondary" onClick={() => { setShowResolveDialog(false); setPendingActions([]); }}>Cancel</button>
              <button className="btn btn-primary" onClick={handleApplyResolutions} disabled={loading}>
                {loading ? 'Applying...' : 'Apply & Regenerate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showCodebasePicker && (
        <FolderPickerModal
          title="Select Codebase Folder"
          initialPath={form.codebasePath || ''}
          onSelect={path => { if (path && path.trim()) update('codebasePath', path.trim()); setShowCodebasePicker(false); }}
          onClose={() => setShowCodebasePicker(false)}
        />
      )}
    </div>
  );
}

function ResultPanel({ result, activeTab, onTabChange, outputDir }) {
  const status = result.status;
  const exec = result.execution_result || {};
  const org = result.organization || {};
  const dup = result.duplicate_result || {};

  const [showRunDialog, setShowRunDialog] = useState(false);
  const [testStructure, setTestStructure] = useState(null);
  const [selectedTests, setSelectedTests] = useState(new Set());
  const [suiteSelected, setSuiteSelected] = useState({});
  const [runLoading, setRunLoading] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState('');

  const execDisplay = runResult || exec;

  async function handleFetchStructure() {
    if (!result.test_file_path) return;
    setRunError('');
    setRunResult(null);
    try {
      const res = await api.getTestStructure(result.test_file_path);
      setTestStructure(res);
      const allTests = new Set();
      const suiteSel = {};
      (res.suites || []).forEach(s => {
        suiteSel[s.name] = true;
        (s.tests || []).forEach(t => allTests.add(t.name));
      });
      setSelectedTests(allTests);
      setSuiteSelected(suiteSel);
      setShowRunDialog(true);
    } catch (e) {
      setRunError(e.message);
    }
  }

  function toggleTest(name) {
    setSelectedTests(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  }

  function toggleSuite(suiteName, tests) {
    const names = (tests || []).map(t => t.name);
    const allSelected = names.every(n => selectedTests.has(n));
    setSelectedTests(prev => {
      const next = new Set(prev);
      names.forEach(n => {
        if (allSelected) next.delete(n); else next.add(n);
      });
      return next;
    });
    setSuiteSelected(prev => ({ ...prev, [suiteName]: !allSelected }));
  }

  async function handleRunSelected() {
    if (selectedTests.size === 0) return;
    setRunLoading(true);
    setRunError('');
    setRunResult(null);
    try {
      const payload = {
        test_file_name: result.test_file_path,
        url: result.test_plan?.url || result.url || '',
        test_names: Array.from(selectedTests),
      };
      const res = await api.runTests(payload);
      setRunResult(res);
      setShowRunDialog(false);
      onTabChange('execution');
    } catch (e) {
      setRunError(e.message);
    }
    setRunLoading(false);
  }

  async function handleRunAll() {
    setRunLoading(true);
    setRunError('');
    setRunResult(null);
    try {
      const payload = {
        test_file_name: result.test_file_path,
        url: result.test_plan?.url || result.url || '',
      };
      const res = await api.runTests(payload);
      setRunResult(res);
      setShowRunDialog(false);
      onTabChange('execution');
    } catch (e) {
      setRunError(e.message);
    }
    setRunLoading(false);
  }

  return (
    <div className="result-panel">
      <div className={`result-banner result-${status}`}>
        <span className="result-status">{status.toUpperCase()}</span>
        <span className="result-message">{result.message}</span>
        {execDisplay.passed !== undefined && (
          <span className="result-stats">
            <span className="stat-passed">&#10003; {execDisplay.passed}</span>
            <span className="stat-failed">&#10007; {execDisplay.failed}</span>
            <span className="stat-skipped">&#8212; {execDisplay.skipped}</span>
          </span>
        )}
      </div>

      {result.test_file_path && (
        <div className="result-file">
          <span>File: {result.test_file_path}</span>
          {(result.report_path || execDisplay.report_path) && (
            <>
              <a href="#" onClick={() => window.electronAPI?.openPath(result.report_path || execDisplay.report_path)} className="report-link">View Report</a>
              <button className="btn btn-sm btn-secondary" onClick={() => api.downloadReport(result.report_path || execDisplay.report_path)} style={{ marginLeft: 8 }}>Download Report</button>
            </>
          )}
          {!showRunDialog && (
            <button className="btn btn-primary btn-sm" onClick={handleFetchStructure} style={{ marginLeft: 12 }}>
              Run Tests
            </button>
          )}
        </div>
      )}

      {result.project_scaffold?.scaffolded && (
        <div className="scaffold-banner">
          <strong>&#9889; Playwright project initialized:</strong> {result.project_scaffold.message}
        </div>
      )}

      {org.module && (
        <div className="org-badges">
          <span className="badge badge-module">{org.module}</span>
          <span className="badge badge-type">{org.test_type}</span>
          <span className="badge badge-priority">{org.priority}</span>
          {org.tags?.map((t, i) => <span key={i} className="badge badge-tag">{t}</span>)}
        </div>
      )}

      {runError && <div className="error-bar">{runError}</div>}

      {showRunDialog && testStructure && (
        <div className="run-dialog">
          <div className="run-dialog-header">
            <h4>Select Tests to Run</h4>
            <span className="text-muted">{testStructure.file}</span>
          </div>
          <div className="run-dialog-actions">
            <button className="btn btn-primary btn-sm" onClick={handleRunSelected} disabled={runLoading || selectedTests.size === 0}>
              {runLoading ? 'Running...' : `Run Selected (${selectedTests.size})`}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleRunAll} disabled={runLoading}>
              Run All
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowRunDialog(false)} disabled={runLoading}>
              Cancel
            </button>
          </div>
          <div className="test-tree">
            {testStructure.suites?.length === 0 && <p className="text-muted">No tests found in this file</p>}
            {testStructure.suites?.map((suite, i) => {
              const allInSuite = (suite.tests || []).map(t => t.name);
              const allSelected = allInSuite.every(n => selectedTests.has(n));
              const someSelected = allInSuite.some(n => selectedTests.has(n));
              return (
                <div key={i} className="test-suite">
                  <label className="suite-label">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={el => { if (el) el.indeterminate = someSelected && !allSelected; }}
                      onChange={() => toggleSuite(suite.name, suite.tests)}
                    />
                    <span className="suite-name">{suite.name}</span>
                    <span className="suite-count">({suite.tests?.length || 0})</span>
                  </label>
                  <div className="test-list">
                    {suite.tests?.map((t, j) => (
                      <label key={j} className="test-label">
                        <input
                          type="checkbox"
                          checked={selectedTests.has(t.name)}
                          onChange={() => toggleTest(t.name)}
                        />
                        <span className="test-name">{t.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {result.healing_result?.healed && (
        <div className="healing-banner">
          <strong>Self-Healed Selectors:</strong>
          {result.healing_result.healed_selectors?.map((h, i) => (
            <div key={i} className="healing-item">
              <span className="healing-old">{h.old}</span>
              <span className="healing-arrow">&rarr;</span>
              <span className="healing-new">{h.new}</span>
            </div>
          ))}
        </div>
      )}

      {dup.has_duplicates && (
        <div className="dup-banner">
          <strong>Duplicate Scenarios Skipped:</strong> {dup.duplicate_matches?.length} found
        </div>
      )}

      <div className="result-tabs">
        {['testPlan', 'locators', 'scenarios', 'testCode', 'execution'].map(tab => (
          <button key={tab} className={`result-tab ${activeTab === tab ? 'active' : ''}`} onClick={() => onTabChange(tab)}>
            {{ testPlan: 'Test Plan', locators: 'Locators', scenarios: 'Scenarios', testCode: 'Test Code', execution: 'Execution' }[tab]}
          </button>
        ))}
      </div>

      <div className="result-content">
        {activeTab === 'testPlan' && (
          <div className="test-plan-panel">
            {result.test_plan ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 className="plan-title" style={{ margin: 0 }}>{result.test_plan.title}</h3>
                  <button
                    className="btn btn-sm btn-secondary"
                    onClick={() => {
                      const plan = result.test_plan;
                      const featureName = (result.organization?.module || plan.title || 'test-plan')
                        .replace(/[^a-zA-Z0-9_-\s]/g, '').trim().replace(/\s+/g, '_').toLowerCase() || 'test-plan';
                      const md = testPlanToMarkdown(plan);
                      const blob = new Blob([md]);
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `${featureName}_test_plan.md`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      setTimeout(() => URL.revokeObjectURL(url), 2000);
                      if (outputDir) {
                        api.exportTestPlan(plan, featureName, outputDir).catch(() => {});
                      }
                    }}
                    title="Download test plan as Markdown file"
                  >
                    Download Test Plan (.md)
                  </button>
                </div>
                {result.test_plan.url && <p className="plan-url"><strong>URL:</strong> {result.test_plan.url}</p>}
                {result.test_plan.overview && <p className="plan-overview">{result.test_plan.overview}</p>}

                {result.test_plan.user_flows?.length > 0 && (
                  <section className="plan-section">
                    <h4>User Flows</h4>
                    <ul className="plan-flows">
                      {result.test_plan.user_flows.map((f, i) => (
                        <li key={i} className="plan-flow-item">
                          <strong>{f.name}</strong>{f.description && <span> — {f.description}</span>}
                          {f.critical && <span className="badge badge-priority" style={{ marginLeft: 8 }}>critical</span>}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                {result.test_plan.scenarios?.length > 0 && (
                  <section className="plan-section">
                    <h4>Scenarios ({result.test_plan.scenarios.length})</h4>
                    <div className="plan-scenarios">
                      {result.test_plan.scenarios.map((s, i) => (
                        <div key={i} className="scenario-card">
                          <div className="plan-scenario-header">
                            <h5>{s.title}</h5>
                            <div className="plan-scenario-badges">
                              <span className="badge badge-priority">{s.priority}</span>
                              <span className="badge badge-type">{s.type}</span>
                              {s.suite && <span className="badge badge-module">{s.suite}</span>}
                            </div>
                          </div>
                          {s.preconditions && <p className="plan-preconditions"><strong>Preconditions:</strong> {s.preconditions}</p>}
                          <ol className="plan-steps">
                            {s.steps?.map((step, j) => <li key={j}>{step.replace(/^\d+\.\s*/, '')}</li>)}
                          </ol>
                          <p className="plan-expected"><strong>Expected:</strong> {s.expected_result}</p>
                          {s.success_criteria?.length > 0 && (
                            <div className="plan-criteria">
                              <strong>Success Criteria:</strong>
                              <ul>{s.success_criteria.map((c, k) => <li key={k}>{c}</li>)}</ul>
                            </div>
                          )}
                          {s.failure_conditions?.length > 0 && (
                            <div className="plan-criteria">
                              <strong>Failure Conditions:</strong>
                              <ul>{s.failure_conditions.map((c, k) => <li key={k}>{c}</li>)}</ul>
                            </div>
                          )}
                          {s.tags?.map((t, k) => <span key={k} className="badge badge-tag">{t}</span>)}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {result.test_plan.coverage_summary && (
                  <section className="plan-section">
                    <h4>Coverage Summary</h4>
                    <p>{result.test_plan.coverage_summary}</p>
                  </section>
                )}

                {result.test_plan.assumptions?.length > 0 && (
                  <section className="plan-section">
                    <h4>Assumptions</h4>
                    <ul>{result.test_plan.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul>
                  </section>
                )}

                {result.test_plan.risks?.length > 0 && (
                  <section className="plan-section">
                    <h4>Risks</h4>
                    <ul>{result.test_plan.risks.map((r, i) => <li key={i}>{r}</li>)}</ul>
                  </section>
                )}
              </>
            ) : (
              <p className="text-muted">No test plan generated. Click <strong>Preview Plan</strong> to generate one.</p>
            )}
          </div>
        )}
        {activeTab === 'locators' && (
          <div>
            {result.page_locators && Object.keys(result.page_locators).length > 0 ? (
              Object.entries(result.page_locators).map(([pageName, pageLocs]) => (
                <div key={pageName} style={{ marginBottom: 16 }}>
                  <h4 style={{ color: 'var(--primary)', marginBottom: 4, textTransform: 'capitalize' }}>{pageName.replace(/_/g, ' ')}</h4>
                  <pre className="code-block" style={{ marginTop: 0 }}>{JSON.stringify(pageLocs, null, 2)}</pre>
                </div>
              ))
            ) : (
              <pre className="code-block">{JSON.stringify(result.locators, null, 2) || 'No locators generated'}</pre>
            )}
          </div>
        )}
        {activeTab === 'scenarios' && (
          <div className="scenarios-list">
            {result.scenarios?.map((s, i) => (
              <div key={i} className="scenario-card">
                <h4>{s.name}</h4>
                <p className="scenario-steps">{s.steps}</p>
                <p className="scenario-expected"><strong>Expected:</strong> {s.expected_result}</p>
              </div>
            )) || <p>No scenarios generated</p>}
          </div>
        )}
        {activeTab === 'testCode' && (
          <pre className="code-block">{result.test_file_path || 'No test code generated'}</pre>
        )}
        {activeTab === 'execution' && (
          <div className="execution-details">
            {runResult && runResult.report_path && (
              <div className="exec-report-link">
                <a href="#" onClick={() => window.electronAPI?.openPath(runResult.report_path)} className="report-link">View HTML Report</a>
                <button className="btn btn-sm btn-secondary" onClick={() => api.downloadReport(runResult.report_path)} style={{ marginLeft: 8 }}>Download HTML Report</button>
              </div>
            )}
            {execDisplay.logs ? (
              <div><h4>Logs</h4><pre className="code-block">{execDisplay.logs}</pre></div>
            ) : (
              <div className="exec-prompt">
                <p className="text-muted">No tests have been run yet.</p>
                {result.test_file_path && (
                  <button className="btn btn-primary" onClick={handleFetchStructure}>
                    Run Tests Now
                  </button>
                )}
              </div>
            )}
            {execDisplay.broken_selectors?.length > 0 && (
              <div><h4>Broken Selectors</h4><pre className="code-block">{JSON.stringify(execDisplay.broken_selectors, null, 2)}</pre></div>
            )}
            {execDisplay.failure_summary && <div><h4>Failure Summary</h4><pre className="code-block">{execDisplay.failure_summary}</pre></div>}
          </div>
        )}
      </div>
    </div>
  );
}

function testPlanToMarkdown(plan) {
  if (!plan) return '# Test Plan\n\nNo test plan generated.\n';
  const lines = [];
  lines.push(`# ${plan.title || 'Test Plan'}\n`);
  if (plan.url) lines.push(`- **URL:** ${plan.url}\n`);
  if (plan.overview) lines.push(`## Overview\n\n${plan.overview}\n`);

  if (plan.user_flows?.length > 0) {
    lines.push('## User Flows\n');
    plan.user_flows.forEach(f => {
      const badge = f.critical ? ' **Critical**' : '';
      lines.push(f.description ? `- **${f.name}** — ${f.description}${badge}` : `- **${f.name}**${badge}`);
    });
    lines.push('');
  }

  if (plan.scenarios?.length > 0) {
    lines.push(`## Scenarios (${plan.scenarios.length})\n`);
    plan.scenarios.forEach((s, i) => {
      const suite = s.suite || '';
      const priority = s.priority || 'medium';
      const stype = s.type || 'happy path';
      lines.push(`### ${i + 1}. ${s.title || `Scenario ${i + 1}`}`);
      lines.push(`**ID:** \`${s.id || `scenario-${i + 1}`}\` | **Suite:** ${suite} | **Priority:** ${priority} | **Type:** ${stype}\n`);
      if (s.preconditions) lines.push(`**Preconditions:** ${s.preconditions}\n`);
      if (s.steps?.length > 0) {
        lines.push('**Steps:**\n');
        s.steps.forEach((step, j) => {
          const clean = step.replace(/^\d+\.\s*/, '');
          lines.push(`  ${j + 1}. ${clean}`);
        });
        lines.push('');
      }
      if (s.expected_result) lines.push(`**Expected Result:** ${s.expected_result}\n`);
      if (s.success_criteria?.length > 0) {
        lines.push('**Success Criteria:**\n');
        s.success_criteria.forEach(c => lines.push(`- ${c}`));
        lines.push('');
      }
      if (s.failure_conditions?.length > 0) {
        lines.push('**Failure Conditions:**\n');
        s.failure_conditions.forEach(c => lines.push(`- ${c}`));
        lines.push('');
      }
      if (s.tags?.length > 0) lines.push(`**Tags:** ${s.tags.join(', ')}\n`);
      lines.push('---\n');
    });
  }

  if (plan.coverage_summary) lines.push(`## Coverage Summary\n\n${plan.coverage_summary}\n`);
  if (plan.assumptions?.length > 0) {
    lines.push('## Assumptions\n');
    plan.assumptions.forEach(a => lines.push(`- ${a}`));
    lines.push('');
  }
  if (plan.risks?.length > 0) {
    lines.push('## Risks\n');
    plan.risks.forEach(r => lines.push(`- ${r}`));
    lines.push('');
  }
  lines.push('---\n*Generated by AI QA Platform*');
  return lines.join('\n');
}

function ManualTestsTab({ settings }) {
  const [activeManualTab, setActiveManualTab] = useState('fresh');
  const [form, setForm] = useState({
    url: '', requirement: '', featureName: '', existingFile: '',
    prdFile: null, confluenceUrl: '', jiraTicketId: '',
  });
  const [result, setResult] = useState(null);
  const [suites, setSuites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { loadSuites(); }, []);

  async function loadSuites() {
    try {
      const res = await api.listManualTests();
      setSuites(res.suites || []);
    } catch (e) { /* ignore */ }
  }

  function update(key, value) { setForm(prev => ({ ...prev, [key]: value })); }

  function getLlmApiKey() {
    switch (settings.llmProvider) {
      case 'anthropic': return settings.anthropicApiKey;
      case 'google': return settings.googleApiKey;
      case 'groq': return settings.groqApiKey;
      case 'opencode': return settings.opencodeApiKey;
      default: return settings.openaiApiKey;
    }
  }

  async function handleGenerate() {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const payload = {
        url: form.url || undefined,
        requirement: form.requirement || undefined,
        feature_name: form.featureName || 'Untitled',
        mode: activeManualTab,
        existing_file: form.existingFile || undefined,
        confluence_url: form.confluenceUrl || undefined,
        jira_ticket_id: form.jiraTicketId || undefined,
        llm_provider: settings.llmProvider || undefined,
        llm_model: settings.llmModel || undefined,
        llm_api_key: getLlmApiKey() || undefined,
        llm_max_tokens: settings.llmMaxTokens || undefined,
      };
      const res = await api.createManualTests(payload);
      setResult(res);
      loadSuites();
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  return (
    <div className="manual-tests-tab">
      <h2>Manual Tests</h2>

      <div className="sub-tabs">
        {[
          { id: 'fresh', label: 'Fresh Generate' },
          { id: 'add', label: 'Add Feature' },
          { id: 'edit', label: 'Edit Tests' },
          { id: 'view', label: 'View Suites' },
        ].map(tab => (
          <button key={tab.id} className={`tab-btn ${activeManualTab === tab.id ? 'active' : ''}`} onClick={() => setActiveManualTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeManualTab !== 'view' ? (
        <div className="generate-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Feature Name</label>
              <input type="text" value={form.featureName} onChange={e => update('featureName', e.target.value)} placeholder="e.g., User Authentication" />
            </div>
            <div className="form-group">
              <label>Application URL (Mandatory)</label>
              <input type="text" value={form.url} onChange={e => update('url', e.target.value)} placeholder="https://example.com" />
            </div>
            <div className="form-group">
              <label>PRD File</label>
              <input type="file" onChange={e => update('prdFile', e.target.files[0])} accept=".pdf,.docx,.txt,.md" />
            </div>
            <div className="form-group">
              <label>Confluence URL</label>
              <input type="text" value={form.confluenceUrl} onChange={e => update('confluenceUrl', e.target.value)} />
            </div>
            <div className="form-group">
              <label>Jira Ticket ID</label>
              <input type="text" value={form.jiraTicketId} onChange={e => update('jiraTicketId', e.target.value)} placeholder="PROJ-123" />
            </div>
            {activeManualTab === 'edit' && (
              <div className="form-group">
                <label>Existing File</label>
                <input type="text" value={form.existingFile} onChange={e => update('existingFile', e.target.value)} placeholder="feature-slug.json" />
              </div>
            )}
            <div className="form-group full-width">
              <label>Requirement Text</label>
              <textarea value={form.requirement} onChange={e => update('requirement', e.target.value)} rows={4} />
            </div>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
              {loading ? 'Generating...' : 'Generate Manual Tests'}
            </button>
          </div>

          {error && <div className="error-bar">{error}</div>}

          {result && (
            <div className="result-panel">
              <div className={`result-banner result-${result.status}`}>
                <span className="result-status">{result.status.toUpperCase()}</span>
                <span className="result-message">{result.message}</span>
                <span className="result-stats">
                  <span>Added: {result.added_count}</span>
                  <span>Edited: {result.edited_count}</span>
                  <span>Total: {result.total_count}</span>
                </span>
              </div>
              {result.file_path && <div className="result-file">File: {result.file_path}</div>}
              <div className="manual-cases">
                {result.test_cases?.map((tc, i) => (
                  <div key={i} className="manual-case-card">
                    <div className="case-header">
                      <h4>{tc.title}</h4>
                      <div className="case-badges">
                        <span className="badge badge-priority">{tc.priority}</span>
                        <span className="badge badge-type">{tc.test_type}</span>
                      </div>
                    </div>
                    <p className="case-preconditions"><strong>Preconditions:</strong> {tc.preconditions}</p>
                    <pre className="case-steps">{tc.steps}</pre>
                    <p className="case-expected"><strong>Expected:</strong> {tc.expected_result}</p>
                    {tc.tags?.map((t, j) => <span key={j} className="badge badge-tag">{t}</span>)}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="suites-list">
          <h3>Test Suites</h3>
          <button className="btn btn-secondary" onClick={loadSuites}>Refresh</button>
          {suites.length === 0 && <p className="text-muted">No test suites yet</p>}
          {suites.map((s, i) => (
            <div key={i} className="suite-card">
              <h4>{s.feature_name}</h4>
              <p className="text-muted">Slug: {s.feature_slug} | Tests: {s.test_count} | Version: {s.version}</p>
              <p className="text-muted">Created: {s.created_at?.slice(0, 10)} | Updated: {s.updated_at?.slice(0, 10)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function UserManualPanel({ onClose, outputDir }) {
  const [activeSection, setActiveSection] = useState('overview');
  const sections = [
    { id: 'overview', label: 'Overview' },
    { id: 'setup', label: 'First-Time Setup' },
    { id: 'providers', label: 'AI Providers' },
    { id: 'fresh', label: 'Fresh Generate' },
    { id: 'add', label: 'Add Feature' },
    { id: 'modify', label: 'Modify Tests' },
    { id: 'manual', label: 'Manual Tests' },
    { id: 'registry', label: 'Test Registry' },
    { id: 'results', label: 'Results Panel' },
    { id: 'settings', label: 'Settings' },
    { id: 'files', label: 'File Types' },
    { id: 'troubleshooting', label: 'Troubleshooting' },
    { id: 'shortcuts', label: 'Shortcuts' },
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ width: 800, height: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="modal-header">
          <h2>User Manual</h2>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Press F1 anytime</span>
            <button className="close-btn" onClick={onClose}>&times;</button>
          </div>
        </div>
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <div style={{ width: 180, borderRight: '1px solid var(--border)', overflowY: 'auto', padding: 8 }}>
            {sections.map(s => (
              <button key={s.id} onClick={() => setActiveSection(s.id)}
                style={{ display: 'block', width: '100%', textAlign: 'left', padding: '6px 10px', background: activeSection === s.id ? 'var(--primary)' : 'transparent', color: activeSection === s.id ? 'white' : 'var(--text-muted)', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12, marginBottom: 2 }}>
                {s.label}
              </button>
            ))}
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
            <SectionContent activeSection={activeSection} outputDir={outputDir} />
          </div>
        </div>
      </div>
    </div>
  );
}

function SectionContent({ activeSection, outputDir }) {
  const s = {
    overview: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Overview</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.8 }}>
           AI QA Platform is an application that automatically generates Playwright TypeScript test files and
          structured manual test cases from natural language requirements, application URLs, PRD documents, API
          specifications, and codebase analysis. It uses AI language models (OpenAI, Anthropic Claude, Google
          Gemini, Groq, or local Ollama models) to analyze inputs, generate test scenarios, produce executable test code,
          run tests, and even self-heal broken selectors when the UI changes.
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.8, marginTop: 12 }}><strong>Key capabilities:</strong></p>
        <ul style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.8, paddingLeft: 20 }}>
          <li>Generate Playwright test files from URLs, requirements, and PRDs</li>
          <li>Create Page Object Models alongside test files</li>
          <li>Auto-classify tests into module folders (auth, checkout, etc.)</li>
          <li>Detect and resolve duplicate scenarios (skip/override/remove)</li>
          <li>Execute tests and self-heal broken selectors</li>
          <li>Generate structured manual test cases</li>
          <li>AI auto-detects input type (raw steps vs requirements)</li>
          <li>Analyze codebase via local path to infer selectors and routes</li>
          <li>Import OpenAPI specs, .env files, and manual test XLSX/CSV as context</li>
          <li>Fetch Jira tickets, sprints, and Confluence pages for additional context</li>
          <li>Preview context and test plan before generating</li>
          <li>Download HTML execution reports with pass/fail/skip stats</li>
           <li>Works with OpenAI, Anthropic, Google Gemini, Groq, local Ollama, or VS Code GitHub Copilot</li>
          <li>Custom model names are saved per provider and persist across sessions</li>
          <li>Ollama models are fetched automatically from the local API</li>
        </ul>
      </section>
    ),
    setup: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>First-Time Setup</h3>
        <ol style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 2, paddingLeft: 20 }}>
          <li>Launch the application by double-clicking the executable</li>
          <li>Wait for the splash screen to disappear (AI engine starts in background)</li>
          <li>Click <strong>Settings</strong> gear icon (top-right) or press <strong>Ctrl+,</strong></li>
           <li>Select <strong>AI Provider</strong> and enter your API key (not needed for Ollama or GitHub Copilot)</li>
          <li>Choose a <strong>Model</strong> from the dropdown</li>
          <li>Set the <strong>Output Directory</strong> in Settings</li>
          <li>Click <strong>Save &amp; Apply</strong></li>
        </ol>
      </section>
    ),
    providers: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>AI Providers</h3>
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: '#818cf8', marginBottom: 4, fontSize: 13 }}>OpenAI</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Get API key from platform.openai.com. Models: gpt-4o (recommended), gpt-4o-mini (cheaper), o3-mini, o4-mini.</p>
        </div>
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: '#818cf8', marginBottom: 4, fontSize: 13 }}>Anthropic Claude</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Get API key from console.anthropic.com. Models: claude-sonnet-4-5, claude-3-7-sonnet, claude-opus-4.</p>
        </div>
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: '#818cf8', marginBottom: 4, fontSize: 13 }}>Google Gemini</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Get API key from aistudio.google.com. Models: gemini-2.0-flash (fast), gemini-2.5-pro (powerful).</p>
        </div>
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: '#818cf8', marginBottom: 4, fontSize: 13 }}>Groq</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Get API key from console.groq.com. Models: llama-3.1-8b-instant, llama-3.3-70b-versatile, llama-4-maverick-17b-128e-instruct, llama-4-scout-instruct, gpt-oss-120b, gpt-oss-20b, gpt-oss-safeguard-20b, groq/compound, groq/compound-mini, whisper-large-v3, whisper-large-v3-turbo, meta-llama/llama-guard-4-12b, moonshotai/kimi-k2-instruct.</p>
        </div>
        <div>
          <h4 style={{ color: '#818cf8', marginBottom: 4, fontSize: 13 }}>Ollama (Local)</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>No API key needed. Install from ollama.com. Default URL: http://localhost:11434. Pre-populated models are listed; models fetched from the local Ollama instance are also shown. Custom models typed in the past appear as well.</p>
        </div>
        <div>
          <h4 style={{ color: '#818cf8', marginBottom: 4, fontSize: 13 }}>VS Code GitHub Copilot</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>No API key required. Uses your existing VS Code GitHub Copilot subscription. The token is auto-detected from <code>COPILOT_GITHUB_TOKEN</code>, <code>GITHUB_TOKEN</code>, or <code>GH_TOKEN</code> environment variables, or the <code>gh</code> CLI. An optional manual token field is available in Settings if auto-detection fails. The token must be a fine-grained PAT with <strong>Copilot Requests</strong> permission (classic <code>ghp_</code> tokens are rejected). Models: gpt-4o, claude-sonnet-4-5, gemini-2.0-flash-001.</p>
        </div>
      </section>
    ),
    fresh: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Fresh Generate</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 12 }}>Creates a complete test suite from scratch. Fill in any combination of inputs below. At minimum, a URL or requirement text is recommended.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Application URL:</strong> The AI crawls this URL to discover page structure, routes, elements, and generate Playwright locators.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Requirement / Steps:</strong> Paste either raw test steps (e.g. "1. Navigate to login | 2. Enter email | 3. Click Sign In") or free-form requirements. The AI automatically detects the input type — raw steps are preserved verbatim, requirements are converted into structured Given/When/Then scenarios.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Optional inputs:</strong></p>
        <ul style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.8, paddingLeft: 20, marginBottom: 8 }}>
          <li><strong>PRD File</strong> &mdash; Upload .pdf, .docx, .txt, .md, .xlsx, or .csv product requirement documents</li>
          <li><strong>Manual Test Cases</strong> &mdash; Import existing manual tests from .xlsx or .csv files</li>
          <li><strong>OpenAPI Spec</strong> &mdash; Upload .yaml or .json API specifications to generate API-level test scenarios</li>
          <li><strong>.env File</strong> &mdash; Upload environment variable files for additional configuration context</li>
          <li><strong>Confluence URL</strong> &mdash; Link to a Confluence page to fetch its content as context</li>
          <li><strong>Jira Ticket ID / Sprint ID / Project Key</strong> &mdash; Fetch Jira issues and sprint data for context</li>
          <li><strong>Codebase Path</strong> &mdash; Point to a local frontend codebase to analyze components, routes, and selectors</li>
        </ul>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Preview Context:</strong> Click to analyze all inputs and display what sources were loaded, routes discovered, elements found, API endpoints detected, and the resolved URL. Useful for verifying the AI is picking up the right information before generating.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Preview Plan:</strong> Click to generate a comprehensive test plan (title, overview, user flows, scenario cards with steps/expected results, success/failure criteria, coverage summary, assumptions, risks) <em>without</em> writing any code. The plan is also shown in the Results Panel's Test Plan tab after generation.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}><strong>Pipeline:</strong> Planner (test plan) &rarr; Context Building &rarr; URL Crawling &rarr; Locator Generation &rarr; Requirement Parsing &rarr; Duplicate Detection &rarr; Resolution (if duplicates found) &rarr; Organization Classification &rarr; Test Code Generation &rarr; File Writing. Tests do <em>not</em> run automatically — click <strong>Run Tests</strong> in the Results Panel to execute.</p>
      </section>
    ),
    add: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Add Feature</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}>Adds new test scenarios to an existing feature. Feature Name is required. Duplicate detection compares new scenarios against the registry.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Duplicate Resolution Dialog:</strong> If duplicates are found, a dialog appears letting you choose per scenario:</p>
        <ul style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 2, paddingLeft: 20 }}>
          <li><strong>Skip</strong> — keep the existing scenario unchanged (default)</li>
          <li><strong>Override</strong> — replace the existing scenario with the new one</li>
          <li><strong>Remove</strong> — delete the existing scenario entirely</li>
        </ul>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Click <strong>Apply &amp; Regenerate</strong> to execute your choices. The organization agent classifies the feature into the correct module folder.</p>
      </section>
    ),
    modify: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Modify Tests</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Updates an existing .spec.ts file. Enter the filename. Changed scenarios are updated, new ones added, unchanged ones preserved.</p>
      </section>
    ),
    manual: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Manual Tests</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}>Generate structured manual test cases with AI. Results show test cards with title, priority, test type, preconditions, step-by-step instructions, expected results, and tags.</p>
        <ul style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 2, paddingLeft: 20 }}>
          <li><strong>Fresh Generate:</strong> Complete suite (happy path, negative, edge case, smoke)</li>
          <li><strong>Add Feature:</strong> New cases to existing suite (skips duplicates)</li>
          <li><strong>Edit Tests:</strong> Update existing cases in a suite</li>
          <li><strong>View Suites:</strong> List all saved suites with feature name, slug, test count, version, and timestamps</li>
        </ul>
      </section>
    ),
    registry: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Test Registry</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}>Deduplication database. Every scenario is stored with name, steps, file path, feature name, and timestamp. Duplicate detector uses 75% similarity threshold.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>View:</strong> Browse all registered scenarios with their feature name, file path, and creation date.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}><strong>Delete:</strong> Remove individual entries via the trash icon. Used when you want to allow re-creation of a scenario that was previously registered.</p>
      </section>
    ),
    results: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Results Panel</h3>
        <ul style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 2, paddingLeft: 20 }}>
          <li><strong>Status banner:</strong> SUCCESS / ERROR with pass/fail/skip counts</li>
          <li><strong>File path</strong> with <strong>View Report</strong> (opens in browser) and <strong>Download Report</strong> (saves HTML file) buttons</li>
          <li><strong>Run Tests button</strong> — opens a test selection dialog listing suites (describe blocks) and individual tests (it blocks) with checkboxes. Toggle entire suites or specific tests, then click <strong>Run Selected (N)</strong> or <strong>Run All</strong>. Results appear in the Execution sub-tab.</li>
          <li><strong>Organization badges:</strong> module, test type, priority, tags</li>
          <li><strong>Self-healing banner:</strong> If broken selectors were found during execution, shows old &rarr; new selector mappings</li>
          <li><strong>Duplicate banner:</strong> Shows how many duplicate scenarios were found during generation</li>
          <li><strong>Sub-tabs:</strong> Test Plan, Locators, Scenarios, Test Code, Execution</li>
          <li><strong>Test Plan tab:</strong> Displays the generated test plan with title, overview, user flows, scenario cards (priority/type/suite badges, steps, expected results, success/failure criteria, tags), coverage summary, assumptions, and risks.</li>
          <li><strong>Locators tab:</strong> Shows the Playwright locators generated for each element from URL crawling</li>
          <li><strong>Scenarios tab:</strong> Lists all generated test scenarios with steps and expected results</li>
          <li><strong>Test Code tab:</strong> Displays the full generated Playwright TypeScript test file</li>
          <li><strong>Execution tab:</strong> Shows run logs, pass/fail/skip stats, broken selectors, failure summary, and <strong>View HTML Report</strong> / <strong>Download HTML Report</strong> buttons. If no tests have been run yet, shows a <strong>Run Tests Now</strong> button.</li>
        </ul>
      </section>
    ),
    settings: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Settings</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>AI Provider:</strong> Choose between OpenAI, Anthropic Claude, Google Gemini, Groq, local Ollama, or VS Code GitHub Copilot. Each provider has its own API key field (except Ollama and GitHub Copilot which need no key). For Ollama, specify the base URL and models are fetched automatically from the local API. For GitHub Copilot, the token is auto-detected from your environment. Select a model from the dropdown. Any custom model name you type is saved automatically and persists across sessions under <strong>customModels</strong> in settings.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Output Directory:</strong> Where all generated files are saved (tests, pages, reports, registry). Browse for native folder picker. Click <strong>Open in Explorer</strong> to view the folder.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Atlassian Integration:</strong> Configure Jira and Confluence credentials (URL, email, API token) to fetch tickets, sprints, and wiki pages as test generation context. Supports both API tokens and Personal Access Tokens (PAT). Click <strong>Save &amp; Apply</strong> and then <strong>Restart AI Engine</strong> for changes to take effect.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, marginBottom: 8 }}><strong>Application:</strong> Restart AI Engine, view version/platform info.</p>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}><strong>About:</strong> App version info, User Manual, GitHub Repository link.</p>
      </section>
    ),
    files: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Generated File Types</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, color: 'var(--text-muted)' }}>
          <thead><tr style={{ borderBottom: '1px solid var(--border)' }}><th style={{ textAlign: 'left', padding: 8 }}>Type</th><th style={{ textAlign: 'left', padding: 8 }}>Ext</th><th style={{ textAlign: 'left', padding: 8 }}>Description</th></tr></thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}>Playwright Test</td><td>.spec.ts</td><td>Executable test file with Page Object pattern and tags</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}>Page Object</td><td>_page.ts</td><td>Typed locators and action methods</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}>HTML Report</td><td>.html</td><td>Execution report with stats and logs</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}>Manual Test Suite</td><td>.json</td><td>Structured manual test cases with title, steps, expected results</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}>Test Registry</td><td>.json</td><td>Deduplication database of all generated scenarios</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}>Uploaded Files</td><td>various</td><td>Uploaded PRD, OpenAPI, .env, and manual test files stored in uploads/</td></tr>
            <tr><td style={{ padding: 8 }}>Test Plan</td><td>inline</td><td>Test plan shown in Results Panel (not saved as file)</td></tr>
          </tbody>
        </table>
      </section>
    ),
    troubleshooting: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Troubleshooting</h3>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>Backend won&apos;t start</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Wait 30s for startup. Check port 8765 is free. Ensure Python 3.10+ and deps installed. Click Restart AI Engine in Settings.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>API key errors</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Verify key in Settings, check credits. For Ollama, ensure ollama serve is running and model is pulled.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>No scenarios generated</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Provide more detailed requirement text. Include URL or codebase path for context. Check AI provider is responding.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>Duplicate resolution dialog stuck</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Each duplicate must have an action selected (Skip, Override, or Remove). Click Apply &amp; Regenerate to proceed, or Cancel to discard all new scenarios.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>Test execution fails</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Install Playwright browsers: npx playwright install. Self-healing fixes broken selectors automatically. Check execution logs for details.</p>
        </div>
        <div>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>Preview Plan returns no result</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Ensure you have entered a requirement or application URL. The planner requires context to generate a meaningful test plan. Check the AI provider is configured correctly in Settings.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>Codebase analysis fails</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Verify the codebase path points to a valid frontend directory. Only .ts, .tsx, .js, .jsx, .vue, .svelte, .astro files are analyzed.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>Jira/Confluence credentials not working</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Verify URL, email, and API token in Settings. For PAT auth, leave email blank and paste the token. Restart AI Engine after saving.</p>
        </div>
        <div style={{ marginBottom: 12 }}>
          <h4 style={{ color: 'var(--text-primary)', marginBottom: 4, fontSize: 13 }}>File upload not working</h4>
          <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6 }}>Supported formats: PDF, DOCX, TXT, MD, XLSX, CSV for documents; YAML, JSON for OpenAPI specs; .env for environment variables.</p>
        </div>
      </section>
    ),
    shortcuts: (
      <section>
        <h3 style={{ color: 'var(--primary)', marginBottom: 12 }}>Keyboard Shortcuts</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, color: 'var(--text-muted)' }}>
          <thead><tr style={{ borderBottom: '1px solid var(--border)' }}><th style={{ textAlign: 'left', padding: 8 }}>Shortcut</th><th style={{ textAlign: 'left', padding: 8 }}>Action</th></tr></thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}><strong>Ctrl+,</strong></td><td>Open Settings</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}><strong>Ctrl+O</strong></td><td>Open output folder</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}><strong>F1</strong></td><td>Open User Manual</td></tr>
            <tr style={{ borderBottom: '1px solid var(--border)' }}><td style={{ padding: 8 }}><strong>F12</strong></td><td>Toggle developer tools</td></tr>
            <tr><td style={{ padding: 8 }}><strong>Ctrl+W</strong></td><td>Close window</td></tr>
          </tbody>
        </table>
      </section>
    ),
  };
  return s[activeSection] || s.overview;
}

function RegistryTab() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadRegistry(); }, []);

  async function loadRegistry() {
    setLoading(true);
    try {
      const res = await api.getRegistry();
      setEntries(res.entries || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleDelete(id) {
    try {
      await api.deleteRegistryEntry(id);
      loadRegistry();
    } catch (e) { console.error(e); }
  }

  return (
    <div className="registry-tab">
      <div className="registry-header">
        <h2>Test Registry</h2>
        <button className="btn btn-secondary" onClick={loadRegistry} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>
      {entries.length === 0 && <p className="text-muted">No registered test scenarios</p>}
      <div className="registry-list">
        {entries.map((e, i) => (
          <div key={e.id} className="registry-card">
            <div className="registry-info">
              <h4>{e.name}</h4>
              <p className="text-muted">Feature: {e.feature_name} | File: {e.test_file}</p>
              <p className="text-muted">Created: {e.created_at?.slice(0, 10)}</p>
            </div>
            <button className="btn btn-danger" onClick={() => handleDelete(e.id)} title="Delete">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 4h12M5 4V2h6v2M3 4l1 10h8l1-10"/>
              </svg>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
