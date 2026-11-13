import { describe, expect, test } from 'vitest';

import { runHead } from '~/routes/-testUtils';
import { Route } from '~/routes/apidocs_.webhooks';

describe('apidocs webhooks route head', () => {
  test('titles the page Webhooks', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Webhooks - The Blue Alliance',
    });
  });
});
