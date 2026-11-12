import { describe, expect, test } from 'vitest';

import { runHead } from '~/routes/-testUtils';
import { Route as BrandRoute } from '~/routes/brand';

describe('brand route head', () => {
  test('titles the page Brand', () => {
    expect(runHead(BrandRoute)?.meta?.[0]).toEqual({
      title: 'The Blue Alliance - Brand',
    });
  });
});
