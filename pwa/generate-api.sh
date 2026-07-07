#!/bin/bash
npx @hey-api/openapi-ts -f openapi-ts/read.config.ts
npx @hey-api/openapi-ts -f openapi-ts/mobile.config.ts
npx @hey-api/openapi-ts -f openapi-ts/nexus.config.ts
npx @hey-api/openapi-ts -f openapi-ts/moderation.config.ts

npm run lint:fix
npm run format:fix
