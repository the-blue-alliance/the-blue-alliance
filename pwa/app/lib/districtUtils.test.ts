import { describe, expect, test } from 'vitest';

import {
  getDistrictColorBorderClass,
  getDistrictColorShadowClass,
} from '~/lib/districtUtils';

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

describe('getDistrictColorBorderClass without a district', () => {
  test('returns no class when the abbreviation is missing', () => {
    expect(getDistrictColorBorderClass(undefined)).toBe('');
  });
});

describe('getDistrictColorShadowClass', () => {
  test('returns an inset shadow in the district color', () => {
    expect(getDistrictColorShadowClass('FIM')).toBe(
      'shadow-[inset_4px_0_0_0_var(--color-district-fim)]',
    );
  });

  test('maps historical aliases to the current district color', () => {
    expect(getDistrictColorShadowClass('mar')).toBe(
      'shadow-[inset_4px_0_0_0_var(--color-district-fma)]',
    );
  });

  test('returns no class for an unknown or missing district', () => {
    expect(getDistrictColorShadowClass('unknown')).toBe('');
    expect(getDistrictColorShadowClass(undefined)).toBe('');
  });
});
