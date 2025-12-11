#!/bin/bash
npx @hey-api/openapi-ts -f openapi-ts/read.config.ts
npx @hey-api/openapi-ts -f openapi-ts/mobile.config.ts

# Define a function to run sed in Docker
docker_sed() {
  docker run --rm -v "$PWD":/work -w /work alpine sed -i "$@"
}

# Replace types using Dockerized sed
docker_sed 's/award_type: number/award_type: AwardType/g' app/api/tba/read/types.gen.ts
docker_sed 's/event_type: number/event_type: EventType/g' app/api/tba/read/types.gen.ts

docker run --rm -v "$PWD":/work -w /work alpine sh -c \
  "sed -i '1i\
import { AwardType } from \"~/lib/api/AwardType\";\
import { EventType } from \"~/lib/api/EventType\";' app/api/tba/read/types.gen.ts"

npm run lint:fix
npm run format:fix
