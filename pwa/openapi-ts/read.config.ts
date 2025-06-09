import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(
    __dirname,
    '../../src/backend/web/static/swagger/api_v3.json',
  ),
  output: {
    format: 'prettier',
    path: 'app/api/tba/',
    lint: 'eslint',
  },
  plugins: [
    '@hey-api/client-fetch',
    '@tanstack/react-query',
    'zod',
    {
      name: '@hey-api/sdk',
      validator: true,
    },
  ],
});
