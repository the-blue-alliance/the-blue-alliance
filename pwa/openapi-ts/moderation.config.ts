import { defineConfig } from '@hey-api/openapi-ts';
import path from 'path';

export default defineConfig({
  input: path.resolve(
    __dirname,
    '../../src/backend/web/static/swagger/api_moderation_v1.json',
  ),
  output: {
    path: 'app/api/tba/moderation/',
  },
  plugins: [
    // Emit real TS enums (with x-enum-varnames from the spec) so suggestion
    // types are referenced as SuggestionType.MEDIA, not loose strings.
    {
      name: '@hey-api/typescript',
      enums: 'typescript',
    },
    '@hey-api/client-fetch',
    '@tanstack/react-query',
  ],
});
