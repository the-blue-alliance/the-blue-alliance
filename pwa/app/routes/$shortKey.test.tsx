import { describe, expect, test } from 'vitest';

import { Route } from '~/routes/$shortKey';

function runBeforeLoad(shortKey: string) {
  return () => Route.options.beforeLoad?.({ params: { shortKey } } as never);
}

describe('short key route', () => {
  test('redirects a team number to the team page', () => {
    expect(runBeforeLoad('254')).toThrow(
      expect.objectContaining({
        options: expect.objectContaining({
          to: '/team/$teamNumber/{-$year}',
          params: { teamNumber: '254' },
          statusCode: 301,
        }),
      }),
    );
  });

  test('redirects an event key to the event page', () => {
    expect(runBeforeLoad('2024miket')).toThrow(
      expect.objectContaining({
        options: expect.objectContaining({
          to: '/event/$eventKey',
          params: { eventKey: '2024miket' },
          statusCode: 301,
        }),
      }),
    );
  });

  test('redirects a district key to the district page', () => {
    expect(runBeforeLoad('2024fim')).toThrow(
      expect.objectContaining({
        options: expect.objectContaining({
          to: '/district/$districtAbbreviation/{-$year}',
          params: { districtAbbreviation: 'fim', year: '2024' },
          statusCode: 301,
        }),
      }),
    );
  });

  test('throws not found for a key that is not a team, event or district', () => {
    expect(runBeforeLoad('abc')).toThrow(
      expect.objectContaining({ isNotFound: true }),
    );
  });
});
