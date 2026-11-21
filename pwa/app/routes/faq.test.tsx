import { describe, expect, test } from 'vitest';

import { runHead } from '~/routes/-testUtils';
import { Route as FaqRoute } from '~/routes/faq';

describe('faq route head', () => {
  test('titles the page Frequently Asked Questions', () => {
    expect(runHead(FaqRoute)?.meta?.[0]).toEqual({
      title: 'Frequently Asked Questions - The Blue Alliance',
    });
  });
});
