import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(__dirname, '../app/api/nexus_spec.json'),
  output: {
    path: 'app/api/nexus/',
  },
  plugins: ['@hey-api/client-fetch', '@tanstack/react-query'],
});
