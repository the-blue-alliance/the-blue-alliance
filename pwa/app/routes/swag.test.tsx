import { expect, test } from 'vitest';

import { Route } from '~/routes/swag';

test('redirects to the TBA swag store', () => {
  expect(() => Route.options.beforeLoad?.({} as never)).toThrow(
    expect.objectContaining({
      options: expect.objectContaining({
        href: 'https://www.amazon.com/s/ref=w_bl_sl_s_ap_web_7141123011?ie=UTF8&node=7141123011&field-brandtextbin=The+Blue+Alliance',
        statusCode: 302,
      }),
    }),
  );
});
