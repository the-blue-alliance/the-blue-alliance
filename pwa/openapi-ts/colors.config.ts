import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(__dirname, '../app/api/colors_spec.json'),
  output: {
    path: 'app/api/colors/',
  },
  plugins: ['@hey-api/client-fetch', '@tanstack/react-query'],
});
