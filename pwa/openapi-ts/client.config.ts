import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(
    __dirname,
    '../../src/backend/web/static/swagger/client_v9.json',
  ),
  output: {
    format: 'prettier',
    path: 'app/api/tba/client/',
    lint: 'eslint',
  },
  plugins: ['@hey-api/client-fetch', '@tanstack/react-query'],
});
