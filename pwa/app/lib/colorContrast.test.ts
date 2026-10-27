import { describe, expect, test } from 'vitest';

import { parseColor } from '~/lib/colorContrast';

describe('parseColor', () => {
  test.each([
    { name: 'with a leading #', input: '#0000ff', expected: '#0000ff' },
    { name: 'without a leading #', input: '0000ff', expected: '#0000ff' },
    { name: 'in three-digit form', input: '#fc0', expected: '#ffcc00' },
    { name: 'in uppercase', input: '#FFCC00', expected: '#ffcc00' },
  ])('reads a hex color $name', ({ input, expected }) => {
    expect(parseColor(input)).toBe(expected);
  });

  test.each([
    { name: 'invalid hex digits', input: '#zzzzzz' },
    { name: 'an empty string', input: '' },
  ])('returns null for $name', ({ input }) => {
    expect(parseColor(input)).toBeNull();
  });
});
