import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, test } from 'vitest';

import {
  CARD_BACKGROUND,
  contrastRatio,
  readableColorOn,
  readableTeamColors,
} from '~/lib/colorContrast';

describe('readableColorOn', () => {
  test('lightens navy on the dark card, keeping it blue', () => {
    expect(readableColorOn('#000080', CARD_BACKGROUND.dark)).toBe('#3a6ce2');
  });

  test('lightens purple on the dark card, keeping it purple', () => {
    expect(readableColorOn('#800080', CARD_BACKGROUND.dark)).toBe('#b445b2');
  });

  test('lightens black on the dark card to a neutral gray', () => {
    expect(readableColorOn('#000000', CARD_BACKGROUND.dark)).toBe('#737373');
  });

  test('darkens white on the light card to a neutral gray', () => {
    expect(readableColorOn('#ffffff', CARD_BACKGROUND.light)).toBe('#949494');
  });

  test('darkens yellow on the light card, keeping it yellow', () => {
    expect(readableColorOn('#ffff00', CARD_BACKGROUND.light)).toBe('#9a9a00');
  });

  test('leaves colors that are already readable unchanged', () => {
    expect(readableColorOn('#0000ff', CARD_BACKGROUND.light)).toBe('#0000ff');
    expect(readableColorOn('#ffff00', CARD_BACKGROUND.dark)).toBe('#ffff00');
    expect(readableColorOn('#ff0000', CARD_BACKGROUND.dark)).toBe('#ff0000');
  });

  test('normalizes shorthand and uppercase hex', () => {
    expect(readableColorOn('#F00', CARD_BACKGROUND.light)).toBe('#ff0000');
  });

  test('returns null for an unparseable color', () => {
    expect(readableColorOn('blue', CARD_BACKGROUND.light)).toBeNull();
  });

  test.each([
    '#0000ff',
    '#000080',
    '#4b0082',
    '#000000',
    '#ffffff',
    '#ffff00',
    '#00ff00',
  ])('%s reaches 3:1 on both cards', (hex) => {
    expect(
      contrastRatio(
        readableColorOn(hex, CARD_BACKGROUND.light)!,
        CARD_BACKGROUND.light,
      ),
    ).toBeGreaterThanOrEqual(3);
    expect(
      contrastRatio(
        readableColorOn(hex, CARD_BACKGROUND.dark)!,
        CARD_BACKGROUND.dark,
      ),
    ).toBeGreaterThanOrEqual(3);
  });
});

describe('readableTeamColors', () => {
  test('returns a variant for each theme', () => {
    expect(readableTeamColors('#000080')).toEqual({
      light: '#000080',
      dark: '#3a6ce2',
    });
  });

  test('returns null for an unparseable color', () => {
    expect(readableTeamColors('')).toBeNull();
  });
});

describe('CARD_BACKGROUND', () => {
  const themeCss = readFileSync(
    resolve(__dirname, '../style/theme.css'),
    'utf8',
  );

  function cardColor(selector: string): number[] {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const rule = new RegExp(`^${escaped} \\{([^}]*)\\}`, 'm').exec(themeCss);
    const card = /--card: oklch\(([^)]*)\);/.exec(rule?.[1] ?? '');
    if (!card) throw new Error(`No --card in ${selector}`);
    return card[1].split(/\s+/).map(Number);
  }

  test('matches the --card colors in theme.css', () => {
    expect(cardColor(':root')).toEqual(CARD_BACKGROUND.light);
    expect(cardColor('.dark')).toEqual(CARD_BACKGROUND.dark);
  });
});
