import { describe, expect, test, vi } from 'vitest';

import {
  DATA_PANELS,
  DATA_PANELS_BY_ID,
  MATCH_RECOMMENDATIONS_PANEL_ID,
} from '~/lib/gameday/dataPanels';
import { isDataPanelId } from '~/lib/gameday/types';

vi.mock('~/components/tba/gameday/MatchRecommendationsPanel', () => ({
  MatchRecommendationsPanel: () => null,
}));

describe('data panels', () => {
  test('the match recommendations panel id carries the data panel prefix', () => {
    expect(isDataPanelId(MATCH_RECOMMENDATIONS_PANEL_ID)).toBe(true);
  });

  test('every panel is indexed by its id', () => {
    expect(Object.keys(DATA_PANELS_BY_ID)).toEqual(
      DATA_PANELS.map((panel) => panel.id),
    );
  });

  test('the match recommendations panel is named for the user', () => {
    expect(DATA_PANELS_BY_ID[MATCH_RECOMMENDATIONS_PANEL_ID].name).toBe(
      'Match Recommendations',
    );
  });
});
