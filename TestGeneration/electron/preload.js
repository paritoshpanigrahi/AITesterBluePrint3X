const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectFolder: () => ipcRenderer.invoke('dialog:openDirectory'),
  getSettings: () => ipcRenderer.invoke('settings:get'),
  saveSettings: (settings) => ipcRenderer.invoke('settings:set', settings),
  restartBackend: () => ipcRenderer.invoke('backend:restart'),
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  openPath: (filePath) => ipcRenderer.invoke('shell:openPath', filePath),
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
  platform: process.platform,
  onOpenSettings: (callback) => {
    ipcRenderer.on('menu:openSettings', () => callback());
  },
  onOpenManual: (callback) => {
    ipcRenderer.on('menu:openManual', () => callback());
  },
});
