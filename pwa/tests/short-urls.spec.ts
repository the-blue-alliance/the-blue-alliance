import { expect, test } from '@playwright/test';

test.describe('short URLs', () => {
  [
    ['a team number', '/254', '/team/254'],
    ['an event key', '/2024miket', '/event/2024miket'],
    ['a district key', '/2024fim', '/district/fim/2024'],
  ].forEach(([name, path, expectedLocation]) => {
    test(`redirects ${name} permanently to ${expectedLocation}`, async ({
      request,
    }) => {
      const response = await request.get(path, { maxRedirects: 0 });

      expect(`${response.status()} ${response.headers()['location']}`).toBe(
        `301 ${expectedLocation}`,
      );
    });
  });

  test('returns not found for a key that is not a team, event or district', async ({
    request,
  }) => {
    const response = await request.get('/notaroute', { maxRedirects: 0 });

    expect(response.status()).toBe(404);
  });
});

test.describe('off-site redirects', () => {
  [
    [
      '/bigquery',
      'https://console.cloud.google.com/bigquery?project=tbatv-prod-hrd&p=tbatv-prod-hrd&d=the_blue_alliance&page=dataset',
    ],
    [
      '/swag',
      'https://www.amazon.com/s/ref=w_bl_sl_s_ap_web_7141123011?ie=UTF8&node=7141123011&field-brandtextbin=The+Blue+Alliance',
    ],
  ].forEach(([path, expectedLocation]) => {
    test(`redirects ${path} to the external site`, async ({ request }) => {
      const response = await request.get(path, { maxRedirects: 0 });

      expect(`${response.status()} ${response.headers()['location']}`).toBe(
        `302 ${expectedLocation}`,
      );
    });
  });
});
