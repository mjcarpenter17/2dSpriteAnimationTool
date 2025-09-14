import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  root: 'src/renderer',
  plugins: [react()],
  build: {
    outDir: '../../dist/renderer',
    emptyOutDir: false,
  },
  resolve: {
    alias: {
      '@core': path.resolve(__dirname, 'src/core'),
    }
  }
});
