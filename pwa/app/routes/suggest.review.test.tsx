import { describe, expect, test } from 'vitest';

import { Route as ReviewListRoute } from '~/routes/suggest.review.$suggestionType';
import { Route as ReviewHomeRoute } from '~/routes/suggest.review.index';

function parse(suggestionType: string) {
  return ReviewListRoute.options.params?.parse?.({ suggestionType } as never);
}

describe('suggestion review list route params', () => {
  test('accepts a known suggestion type', () => {
    expect(parse('media')).toEqual({ suggestionType: 'media' });
  });

  test('throws not-found for an unknown suggestion type', () => {
    expect(() => parse('bogus')).toThrow(
      expect.objectContaining({ isNotFound: true }),
    );
  });
});

describe('suggestion review home route', () => {
  test('declares its page component', () => {
    expect(ReviewHomeRoute.options.component).toBeTypeOf('function');
  });
});
