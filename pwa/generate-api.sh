#!/bin/bash
npx oazapfts ../src/backend/web/static/swagger/api_v3.json --argumentStyle=object > app/api/v3.ts
sed -i 's/award_type: number/award_type: AwardType/g' app/api/v3.ts
sed -i 's/event_type: number/event_type: EventType/g' app/api/v3.ts
sed -i '1i\
import { AwardType } from '"'"'~/lib/api/AwardType'"'"';\
import { EventType } from '"'"'~/lib/api/EventType'"'"';' app/api/v3.ts
npm run format:fix
