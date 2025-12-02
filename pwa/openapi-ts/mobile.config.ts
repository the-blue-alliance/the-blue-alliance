import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(
    __dirname,
    '../../src/backend/web/static/swagger/client_v9.json',
  ),
  output: {
    path: 'app/api/tba/mobile/',
  },
  plugins: ['@hey-api/client-fetch', '@tanstack/react-query'],
});
