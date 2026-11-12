import { Temporal } from 'temporal-polyfill';

import { getEvent, getEventMatches } from '~/api/tba/read';
import { buildEventFeed } from '~/lib/eventFeed';
import { eventCacheControlHeaders, isValidEventKey } from '~/lib/eventUtils';

export async function eventFeedResponse(eventKey: string): Promise<Response> {
  if (!isValidEventKey(eventKey)) {
    return new Response('Not found', { status: 404 });
  }

  const path = { event_key: eventKey };
  const [{ data: event }, { data: matches }] = await Promise.all([
    getEvent({ path }),
    getEventMatches({ path }),
  ]);
  if (!event) {
    return new Response('Not found', { status: 404 });
  }

  return new Response(
    buildEventFeed(event, matches ?? [], Temporal.Now.instant()),
    {
      headers: {
        'Content-Type': 'application/xml; charset=UTF-8',
        ...eventCacheControlHeaders(event),
      },
    },
  );
}
