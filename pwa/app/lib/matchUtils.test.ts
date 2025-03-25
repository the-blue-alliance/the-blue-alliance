import { describe, expect, test } from 'vitest';

import { isValidMatchKey } from '~/lib/matchUtils';

describe.concurrent('isValidMatchKey', () => {
  test.each([
    '2019nyny_qm1',
    '2010ct_sf1m3',
    '2022on306_qm15',
    '2023week0_sf13m1',
    '2023bc_ef10m1',
    '2023bc_qf10m1',
  ])('valid match key', (key) => {
    expect(isValidMatchKey(key)).toBe(true);
  });

  test.each([
    'frc177',
    '2010ct_qm1m1',
    '2010ctf1m1',
    '2010ct_f1',
    '2022on_306_qm15',
    '2023week0_sf130m1',
    '2023bc_f10m1',
    '2023bc_ef123m1',
    '2023bc_qf123m1',
  ])('invalid match key', (key) => {
    expect(isValidMatchKey(key)).toBe(false);
  });
});
