const { app, BrowserWindow, ipcMain, dialog, Menu, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const Store = require('electron-store');
const windowStateKeeper = require('electron-window-state');
const BackendManager = require('./backend-manager');

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

const store = new Store({
  schema: {
    llmProvider: { type: 'string', default: 'openai' },
    llmModel: { type: 'string', default: 'gpt-4o' },
    openaiApiKey: { type: 'string', default: '' },
    anthropicApiKey: { type: 'string', default: '' },
    googleApiKey: { type: 'string', default: '' },
    ollamaBaseUrl: { type: 'string', default: 'http://localhost:11434' },
    outputDir: { type: 'string', default: '' },
    theme: { type: 'string', default: 'dark' },
    windowX: { type: 'number', default: undefined },
    windowY: { type: 'number', default: undefined },
    windowWidth: { type: 'number', default: 1400 },
    windowHeight: { type: 'number', default: 900 },
    jiraUrl: { type: 'string', default: '' },
    jiraEmail: { type: 'string', default: '' },
    jiraApiToken: { type: 'string', default: '' },
    confluenceUrl: { type: 'string', default: '' },
    confluenceEmail: { type: 'string', default: '' },
    confluenceApiToken: { type: 'string', default: '' },
  },
});

let mainWindow = null;
let splashWindow = null;
const backendManager = new BackendManager(store);

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 500,
    height: 300,
    frame: false,
    transparent: true,
    resizable: false,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  splashWindow.loadURL(`data:text/html;charset=utf-8,
    <html>
    <head><style>
      body {
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100vh;
        background: #0f172a;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        flex-direction: column;
      }
      .spinner {
        width: 48px;
        height: 48px;
        border: 4px solid #334155;
        border-top: 4px solid #6366f1;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 24px;
      }
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      h2 { font-weight: 400; margin: 0; }
      p { color: #94a3b8; margin-top: 8px; font-size: 14px; }
    </style></head>
    <body>
      <div class="spinner"></div>
      <h2>Starting AI engine...</h2>
      <p>Initializing backend services</p>
    </body>
    </html>
  `);
}

function createMainWindow() {
  const mainWindowState = windowStateKeeper({
    defaultWidth: 1400,
    defaultHeight: 900,
  });

  mainWindow = new BrowserWindow({
    x: mainWindowState.x,
    y: mainWindowState.y,
    width: mainWindowState.width,
    height: mainWindowState.height,
    minWidth: 1100,
    minHeight: 700,
    title: 'AI QA Platform',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindowState.manage(mainWindow);

  const frontendDist = path.join(__dirname, '..', 'frontend', 'dist', 'index.html');
  if (isDev) {
    mainWindow.loadURL('http://localhost:5175');
  } else {
    mainWindow.loadFile(frontendDist);
  }

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('menu:openSettings');
            }
          },
        },
        {
          label: 'Open Output Folder',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            const outputDir = store.get('outputDir');
            if (outputDir) {
              shell.openPath(outputDir);
            }
          },
        },
        { type: 'separator' },
        { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'User Manual',
          accelerator: 'F1',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('menu:openManual');
            }
          },
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About AI QA Platform',
              message: 'AI QA Platform v' + app.getVersion(),
              detail: 'Automated test generation and execution platform powered by AI.\n\nBuilt with Electron, React, and Python.',
            });
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function setupIPC() {
  ipcMain.handle('dialog:openDirectory', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory'],
    });
    if (result.canceled || result.filePaths.length === 0) return null;
    return result.filePaths[0];
  });

  ipcMain.handle('settings:get', async () => {
    return store.store;
  });

  ipcMain.handle('settings:set', async (event, settings) => {
    for (const [key, value] of Object.entries(settings)) {
      store.set(key, value);
    }
    return { success: true };
  });

  ipcMain.handle('backend:restart', async () => {
    await backendManager.stop();
    const env = buildBackendEnv();
    await backendManager.start(env);
    return { success: true };
  });

  ipcMain.handle('app:getVersion', async () => {
    return app.getVersion();
  });

  ipcMain.handle('shell:openPath', async (event, filePath) => {
    return shell.openPath(filePath);
  });

  ipcMain.handle('shell:openExternal', async (event, url) => {
    return shell.openExternal(url);
  });

  ipcMain.handle('menu:openManual', async () => {
    if (mainWindow) {
      mainWindow.webContents.send('menu:openManual');
    }
    return { success: true };
  });
}

function buildBackendEnv() {
  return {
    PORT: '8765',
    LLM_PROVIDER: store.get('llmProvider'),
    LLM_BASE_URL: getLlmBaseUrl(),
    OPENAI_API_KEY: getApiKey(),
    OPENAI_MODEL: store.get('llmModel'),
    OUTPUT_DIR: store.get('outputDir') || '',
    JIRA_URL: store.get('jiraUrl') || '',
    JIRA_EMAIL: store.get('jiraEmail') || '',
    JIRA_API_TOKEN: store.get('jiraApiToken') || '',
    CONFLUENCE_URL: store.get('confluenceUrl') || '',
    CONFLUENCE_EMAIL: store.get('confluenceEmail') || '',
    CONFLUENCE_API_TOKEN: store.get('confluenceApiToken') || '',
  };
}

function getLlmBaseUrl() {
  const provider = store.get('llmProvider');
  switch (provider) {
    case 'anthropic':
      return 'https://api.anthropic.com/v1';
    case 'google':
      return 'https://generativelanguage.googleapis.com/v1beta/openai/';
    case 'groq':
      return 'https://api.groq.com/openai/v1';
    case 'github-copilot':
      return 'https://api.githubcopilot.com/v1';
    case 'ollama':
      return store.get('ollamaBaseUrl') + '/v1';
    case 'openai':
    default:
      return 'https://api.openai.com/v1';
  }
}

function getGitHubToken() {
  const stored = store.get('githubCopilotToken') || '';
  if (stored) return stored;
  const envToken = process.env.COPILOT_GITHUB_TOKEN || process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
  if (envToken) return envToken;
  try {
    return require('child_process').execSync('gh auth token', { encoding: 'utf8', timeout: 5000 }).trim();
  } catch {
    return '';
  }
}

function getApiKey() {
  const provider = store.get('llmProvider');
  switch (provider) {
    case 'anthropic':
      return store.get('anthropicApiKey');
    case 'google':
      return store.get('googleApiKey');
    case 'groq':
      return store.get('groqApiKey');
    case 'github-copilot':
      return getGitHubToken();
    case 'ollama':
      return '';
    case 'openai':
    default:
      return store.get('openaiApiKey');
  }
}

app.whenReady().then(async () => {
  createMenu();
  setupIPC();

  const env = buildBackendEnv();

  if (!isDev) {
    createSplashWindow();
    try {
      await backendManager.start(env, isDev);
    } catch (err) {
      console.error('Backend start warning (non-fatal):', err);
    }
  } else {
    backendManager.start(env, isDev).catch(err => {
      console.error('Backend start warning (non-fatal):', err);
    });
  }

  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', async () => {
  await backendManager.stop();
});
