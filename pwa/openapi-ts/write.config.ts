import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(
    __dirname,
    '../../src/backend/web/static/swagger/api_trusted_v1.json',
  ),
  output: {
    format: 'prettier',
    path: 'app/api/tba/write/',
    lint: 'eslint',
  },
  plugins: ['@hey-api/client-fetch'],
});
