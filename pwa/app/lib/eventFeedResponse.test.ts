import { describe, expect, test, vi } from 'vitest';

import { eventFeedResponse } from '~/lib/eventFeedResponse';

const mocks = vi.hoisted(() => ({
  getEvent: vi.fn<() => Promise<unknown>>(),
  getEventMatches: vi.fn<() => Promise<unknown>>(),
}));

vi.mock('~/api/tba/read', async (importOriginal) => ({
  ...(await importOriginal<typeof import('~/api/tba/read')>()),
  ...mocks,
}));

const EVENT = {
  key: '2024casj',
  name: 'Silicon Valley Regional',
  year: 2024,
  playoff_type: null,
};

describe('eventFeedResponse', () => {
  test('responds not found for an invalid event key', async () => {
    const response = await eventFeedResponse('not-an-event');
    expect(response.status).toBe(404);
  });

  test('responds not found when the event does not exist', async () => {
    mocks.getEvent.mockResolvedValue({ data: undefined });
    mocks.getEventMatches.mockResolvedValue({ data: undefined });
    const response = await eventFeedResponse('2024casj');
    expect(response.status).toBe(404);
  });

  test('serves XML for an existing event', async () => {
    mocks.getEvent.mockResolvedValue({ data: EVENT });
    mocks.getEventMatches.mockResolvedValue({ data: [] });
    const response = await eventFeedResponse('2024casj');
    expect(response.headers.get('Content-Type')).toBe(
      'application/xml; charset=UTF-8',
    );
  });

  test('serves the event name in the feed body', async () => {
    mocks.getEvent.mockResolvedValue({ data: EVENT });
    mocks.getEventMatches.mockResolvedValue({ data: [] });
    const response = await eventFeedResponse('2024casj');
    expect(await response.text()).toContain(
      '<title>Silicon Valley Regional 2024</title>',
    );
  });
});
