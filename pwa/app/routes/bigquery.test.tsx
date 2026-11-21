import { expect, test } from 'vitest';

import { Route } from '~/routes/bigquery';

test('redirects to the BigQuery dataset console', () => {
  expect(() => Route.options.beforeLoad?.({} as never)).toThrow(
    expect.objectContaining({
      options: expect.objectContaining({
        href: 'https://console.cloud.google.com/bigquery?project=tbatv-prod-hrd&p=tbatv-prod-hrd&d=the_blue_alliance&page=dataset',
        statusCode: 302,
      }),
    }),
  );
});
