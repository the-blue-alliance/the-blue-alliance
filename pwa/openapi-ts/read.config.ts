import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: '../src/backend/web/static/swagger/api_v3.json',
  output: {
    path: 'app/api/tba/read/',
  },
  plugins: [
    {
      name: '@hey-api/typescript',
      enums: 'typescript',
    },
    '@hey-api/client-fetch',
    '@tanstack/react-query',
    {
      name: 'zod',
      dates: {
        offset: true,
      },
    },
    {
      name: '@hey-api/sdk',
      validator: true,
    },
  ],
});
