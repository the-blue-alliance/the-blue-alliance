import { MatchRecommendationsPanel } from '~/components/tba/gameday/MatchRecommendationsPanel';
import {
  DATA_PANEL_ID_PREFIX,
  type GamedayDataPanelContent,
} from '~/lib/gameday/types';

export const MATCH_RECOMMENDATIONS_PANEL_ID = `${DATA_PANEL_ID_PREFIX}match-recommendations`;

export const DATA_PANELS: GamedayDataPanelContent[] = [
  {
    type: 'data-panel',
    id: MATCH_RECOMMENDATIONS_PANEL_ID,
    name: 'Match Recommendations',
    component: MatchRecommendationsPanel,
  },
];

export const DATA_PANELS_BY_ID = Object.fromEntries(
  DATA_PANELS.map((panel) => [panel.id, panel]),
) as Record<string, GamedayDataPanelContent>;
