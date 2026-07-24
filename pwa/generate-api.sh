#!/bin/bash
npx @hey-api/openapi-ts -f openapi-ts/read.config.ts
npx @hey-api/openapi-ts -f openapi-ts/mobile.config.ts
npx @hey-api/openapi-ts -f openapi-ts/nexus.config.ts
npx @hey-api/openapi-ts -f openapi-ts/colors.config.ts

pnpm exec prettier --write app/api/tba/read app/api/tba/mobile app/api/nexus app/api/colors
