#!/bin/bash
set -e

# Generate the TypeScript API client
npx oazapfts ../src/backend/web/static/swagger/api_v3.json --argumentStyle=object > app/api/v3.ts

# Define a function to run sed in Docker
docker_sed() {
  docker run --rm -v "$PWD":/work -w /work alpine sed -i "$@"
}

# Replace types using Dockerized sed
docker_sed 's/award_type: number/award_type: AwardType/g' app/api/v3.ts
docker_sed 's/event_type: number/event_type: EventType/g' app/api/v3.ts

# Add imports to the top of the file
docker run --rm -v "$PWD":/work -w /work alpine sh -c \
  "sed -i '1i\
import { AwardType } from \"~/lib/api/AwardType\";\
import { EventType } from \"~/lib/api/EventType\";' app/api/v3.ts"

# Format the resulting file
npm run format:fix