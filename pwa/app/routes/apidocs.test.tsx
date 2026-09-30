import { describe, expect, test } from 'vitest';

import { runHead } from '~/routes/-testUtils';
import { Route as ApiDocsRoute } from '~/routes/apidocs';
import { Route as ApiDocsV3Route } from '~/routes/apidocs_.v3';

describe('apidocs route head', () => {
  test('titles the page Developer APIs', () => {
    expect(runHead(ApiDocsRoute)?.meta?.[0]).toEqual({
      title: 'Developer APIs - The Blue Alliance',
    });
  });
});

describe('apidocs v3 route head', () => {
  test('titles the page Read API (v3)', () => {
    expect(runHead(ApiDocsV3Route)?.meta?.[0]).toEqual({
      title: 'Read API (v3) - The Blue Alliance',
    });
  });

  test('loads the Scalar stylesheet', () => {
    expect(runHead(ApiDocsV3Route)?.links).toEqual([
      { rel: 'stylesheet', href: expect.any(String) },
    ]);
  });
});
