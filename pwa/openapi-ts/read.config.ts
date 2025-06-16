import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../src/backend/web/static/swagger/api_v3.json',
  output: {
    format: 'prettier',
    path: 'app/api/tba/',
    lint: 'eslint',
  },
  plugins: [
    {
      name: '@hey-api/typescript',
      enums: 'typescript',
      exportInlineEnums: true,
    },
    '@hey-api/client-fetch',
    '@tanstack/react-query',
    'zod',
    {
      name: '@hey-api/sdk',
      validator: true,
    },
  ],
});
