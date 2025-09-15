import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('api', {
  openSheetListener: (cb: (data: { path: string }) => void) => {
    ipcRenderer.on('sheet:open', (_e, data) => cb(data));
  },
  onThemeChanged: (cb: (theme: 'light' | 'dark') => void) => {
    ipcRenderer.on('theme:changed', (_e, theme) => cb(theme));
  },
  invoke: (channel: string, ...args: any[]) => ipcRenderer.invoke(channel, ...args),
  send: (channel: string, ...args: any[]) => ipcRenderer.send(channel, ...args)
});

declare global {
  interface Window { 
    api: { 
      openSheetListener(cb: (data: { path: string }) => void): void; 
      onThemeChanged(cb: (theme: 'light' | 'dark') => void): void;
      invoke(channel: string, ...args:any[]): Promise<any>; 
      send(channel: string, ...args:any[]): void;
    } 
  }
}
