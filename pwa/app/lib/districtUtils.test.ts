import { describe, expect, test } from 'vitest';

import { getDistrictColorBorderClass } from '~/lib/districtUtils';

describe('getDistrictColorBorderClass', () => {
  test('returns the district color class', () => {
    expect(getDistrictColorBorderClass('fim')).toBe('border-l-district-fim');
  });

  test('normalizes uppercase abbreviations', () => {
    expect(getDistrictColorBorderClass('FIM')).toBe('border-l-district-fim');
  });

  test('maps historical aliases to the current district color', () => {
    expect(getDistrictColorBorderClass('mar')).toBe('border-l-district-fma');
  });

  test('returns no class for an unknown district', () => {
    expect(getDistrictColorBorderClass('unknown')).toBe('');
  });
});
