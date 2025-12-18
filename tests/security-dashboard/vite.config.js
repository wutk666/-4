import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cssInjectedByJsPlugin from 'vite-plugin-css-injected-by-js';
import path from 'path';

export default defineConfig(({ mode }) => {
  const isProd = mode === 'production';

  return {
    plugins: [react(), cssInjectedByJsPlugin()],
    base: isProd ? '/static/dashboard/' : '/',
    build: {
      outDir: path.resolve(__dirname, '../../app/static/dashboard'),
      emptyOutDir: true,
      sourcemap: false,
      cssCodeSplit: false,
      rollupOptions: {
        output: {
          entryFileNames: 'dashboard.js',
          chunkFileNames: 'dashboard.js',
          assetFileNames: 'dashboard.[ext]',
          inlineDynamicImports: true,
          manualChunks: undefined,
        },
      },
    },
    server: {
      port: 5173,
      strictPort: true,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:5000',
          changeOrigin: true,
        },
        '/static': {
          target: 'http://127.0.0.1:5000',
          changeOrigin: true,
        },
      },
    },
  };
});
