import { HttpResponse } from 'msw';
import { describe, expect, test } from 'vitest';

import { getEvent, getEventMatches } from '~/api/tba/read';
import { eventFeedResponse } from '~/lib/eventFeedResponse';
import { makeEvent } from '~/test/factories';
import { mockTbaApi, mockTbaApiWith } from '~/test/msw';

const PATH = { path: { event_key: '2024casj' } };

function mockEvent() {
  mockTbaApi(
    getEvent,
    PATH,
    makeEvent({ key: '2024casj', name: 'Silicon Valley Regional', year: 2024 }),
  );
  mockTbaApi(getEventMatches, PATH, []);
}

describe('eventFeedResponse', () => {
  test('responds not found for an invalid event key', async () => {
    const response = await eventFeedResponse('not-an-event');
    expect(response.status).toBe(404);
  });

  test('responds not found when the event does not exist', async () => {
    mockTbaApiWith(
      getEvent,
      PATH,
      () => new HttpResponse(null, { status: 404 }),
    );
    mockTbaApiWith(
      getEventMatches,
      PATH,
      () => new HttpResponse(null, { status: 404 }),
    );
    const response = await eventFeedResponse('2024casj');
    expect(response.status).toBe(404);
  });

  test('serves XML for an existing event', async () => {
    mockEvent();
    const response = await eventFeedResponse('2024casj');
    expect(response.headers.get('Content-Type')).toBe(
      'application/xml; charset=UTF-8',
    );
  });

  test('serves the event name in the feed body', async () => {
    mockEvent();
    const response = await eventFeedResponse('2024casj');
    expect(await response.text()).toContain(
      '<title>Silicon Valley Regional 2024</title>',
    );
  });
});
