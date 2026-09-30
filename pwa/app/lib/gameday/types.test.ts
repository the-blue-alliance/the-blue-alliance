import { describe, expect, test } from 'vitest';

import { getWebcastId, isDataPanelId } from '~/lib/gameday/types';

describe('isDataPanelId', () => {
  test('recognises data panel ids', () => {
    expect(isDataPanelId('data-panel:match-recommendations')).toBe(true);
  });

  test('rejects webcast ids', () => {
    expect(isDataPanelId('2024casj-0')).toBe(false);
  });
});

describe('getWebcastId', () => {
  test('joins the event key and webcast index', () => {
    expect(getWebcastId('2024casj', 0)).toBe('2024casj-0');
  });
});
