import { describe, expect, test } from 'vitest';

import { ApiError, mapClientError } from '~/lib/apiError';

describe.concurrent('mapClientError', () => {
  test('maps a non-OK response to an ApiError with the matching status', () => {
    const response = new Response(null, {
      status: 404,
      statusText: 'Not Found',
    });
    const result = mapClientError(new Error('boom'), response);

    expect(result).toBeInstanceOf(ApiError);
    expect((result as ApiError).status).toEqual(404);
    expect((result as ApiError).message).toEqual('Not Found');
  });

  test('preserves the original error when the response is OK (e.g. a body parse/validation failure on a 2xx)', () => {
    const response = new Response(null, { status: 200 });
    const error = new Error('invalid response shape');

    expect(mapClientError(error, response)).toBe(error);
  });

  test('preserves the original error when there is no response (network failure)', () => {
    const error = new Error('network error');

    expect(mapClientError(error, undefined)).toBe(error);
  });
});
