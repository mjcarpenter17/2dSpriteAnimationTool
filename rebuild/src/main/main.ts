import { app, BrowserWindow, dialog, ipcMain, Menu } from 'electron';
import { PreferencesManager } from '../core/PreferencesManager';
import { readFile } from 'fs/promises';
import path from 'path';

let mainWindow: BrowserWindow | null = null;
const prefs = new PreferencesManager();

function createWindow() {
  const { window_width, window_height } = prefs.get().layout;
  mainWindow = new BrowserWindow({
    width: window_width,
    height: window_height,
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.js')
    }
  });
  const devUrl = 'http://localhost:5173';
  const prodIndex = `file://${path.join(__dirname, '../../renderer/index.html')}`;
  const target = (process.env.NODE_ENV !== 'production') ? (process.env.VITE_DEV_SERVER_URL || devUrl) : prodIndex;
  console.log('[main] loading URL', target);
  mainWindow.loadURL(target).catch(err=>console.error('[main] loadURL error', err));
  mainWindow.webContents.on('did-fail-load', (_e, ec, desc) => {
    console.error('[main] did-fail-load', ec, desc);
  });
  mainWindow.webContents.on('did-finish-load', ()=>{
    console.log('[main] did-finish-load');
  });
  if (process.env.NODE_ENV !== 'production') {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }
  mainWindow.on('close', () => {
    const b = mainWindow!.getBounds();
    const data = prefs.get();
    data.layout.window_width = b.width;
    data.layout.window_height = b.height;
    prefs.save();
  });
}

function buildMenu() {
  const toggleDarkLabel = prefs.getTheme() === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        { label: 'Open...', accelerator: 'Ctrl+O', click: async () => {
          if (!mainWindow) return;
          const res = await dialog.showOpenDialog(mainWindow, { filters: [{ name: 'Images', extensions: ['png'] }], properties: ['openFile'] });
          if (!res.canceled && res.filePaths[0]) {
            const imgPath = res.filePaths[0];
            prefs.addRecentSheet(imgPath);
            mainWindow.webContents.send('sheet:open', { path: imgPath });
          }
        }},
        { type: 'separator' },
        { role: 'quit' }
      ]
    },
    { label: 'Edit', submenu: [ { role: 'copy' } ] },
    { label: 'View', submenu: [ 
      { role: 'reload' }, 
      { role: 'toggleDevTools' },
      { type: 'separator' },
      { 
        id: 'toggle-dark-mode',
        label: toggleDarkLabel,
        click: () => {
          const next = prefs.getTheme() === 'dark' ? 'light' : 'dark';
          prefs.setTheme(next);
          if (mainWindow) mainWindow.webContents.send('theme:changed', next);
          buildMenu();
        }
      }
    ] },
    { label: 'Animation', submenu: [] },
    { label: 'Help', submenu: [ { label: 'About', click: () => dialog.showMessageBox({ message: 'AnimationViewer Rebuild Shell' }) } ] }
  ];
  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(() => {
  buildMenu();
  createWindow();
  const last = prefs.get().file_management.last_active_sheet;
  if (last && mainWindow) {
    // Defer to allow renderer preload listener to attach
    setTimeout(()=> mainWindow && mainWindow.webContents.send('sheet:open', { path: last }), 300);
  }
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });

ipcMain.handle('file:readBinary', async (_e, p: string) => {
  const data = await readFile(p);
  return data.buffer;
});

ipcMain.on('prefs:setLastActiveSheet', (_e, path: string | null) => {
  prefs.setLastActiveSheet(path || null);
});

ipcMain.handle('prefs:getPivotStrategy', () => {
  return prefs.getPivotStrategy();
});

ipcMain.on('prefs:setPivotStrategy', (_e, strategy: string) => {
  prefs.setPivotStrategy(strategy);
});

ipcMain.handle('overrides:getAll', () => {
  return prefs.getOverrides();
});

ipcMain.on('overrides:setAll', (_e, payload: any) => {
  // Trust renderer minimally: basic shape validation
  if (payload && typeof payload === 'object') {
    prefs.setOverrides(payload);
  }
});

ipcMain.on('debug:log', (_e, msg: any, ...rest: any[]) => {
  console.log('[renderer-log]', msg, ...rest);
});

ipcMain.handle('theme:get', () => {
  return prefs.getTheme();
});

ipcMain.on('theme:set', (_e, theme: 'light' | 'dark') => {
  prefs.setTheme(theme);
  if (mainWindow) mainWindow.webContents.send('theme:changed', prefs.getTheme());
  buildMenu();
});
