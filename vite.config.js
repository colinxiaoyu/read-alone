import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url)).replace(/\/$/, '');
const health = (server) => {
  server.middlewares.use('/__read_alone__', (_request, response) => {
    response.setHeader('Content-Type', 'application/json');
    response.end(JSON.stringify({ application: 'read-alone', runtime: 'react-vite', root }));
  });
};

export default defineConfig({
  plugins: [react(), { name: 'read-alone-health', configureServer: health, configurePreviewServer: health }],
  server: { host: '127.0.0.1', port: 8765 },
  preview: { host: '127.0.0.1', port: 8765 },
});
