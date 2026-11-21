import { createFileRoute } from '@tanstack/react-router';

import { eventFeedResponse } from '~/lib/eventFeedResponse';

export const Route = createFileRoute('/event/$eventKey_/feed')({
  server: {
    handlers: {
      GET: ({ params }) => eventFeedResponse(params.eventKey),
    },
  },
});
