import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type HubScore2026,
  type Match,
  type MatchScoreBreakdown2026,
  type MatchScoreBreakdown2026Alliance,
  TowerRobot2026,
} from '~/api/tba/read';
import ScoreByShift2026 from '~/components/tba/match/scoreByShift2026';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Recharts sizes the chart from the container's bounding box, which jsdom
// reports as 0x0; give the container a real size (and leave every other
// element, such as the measured tick text, at zero) so the chart lays out.
const chartBox: DOMRect = {
  x: 0,
  y: 0,
  top: 0,
  left: 0,
  right: 640,
  bottom: 360,
  width: 640,
  height: 360,
  toJSON: () => ({}),
};
const emptyBox: DOMRect = {
  x: 0,
  y: 0,
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  width: 0,
  height: 0,
  toJSON: () => ({}),
};

// Recharts only draws point labels once its entry animation finishes, which
// never happens in jsdom. It honours prefers-reduced-motion by skipping the
// animation, so the tests view the chart as a reduced-motion user.
function reducedMotionMatchMedia(query: string): MediaQueryList {
  return {
    matches: query === '(prefers-reduced-motion: reduce)',
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  };
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

// vitest restores spies and stubs between tests, so re-apply per test.
beforeEach(() => {
  vi.stubGlobal('matchMedia', reducedMotionMatchMedia);
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(
    function (this: HTMLElement) {
      return this.classList.contains('recharts-responsive-container')
        ? chartBox
        : emptyBox;
    },
  );
});

function makeHubScore(overrides: Partial<HubScore2026> = {}): HubScore2026 {
  return {
    autoCount: 12,
    autoPoints: 12,
    transitionCount: 4,
    transitionPoints: 4,
    shift1Count: 10,
    shift1Points: 10,
    shift2Count: 20,
    shift2Points: 20,
    shift3Count: 15,
    shift3Points: 15,
    shift4Count: 5,
    shift4Points: 5,
    endgameCount: 7,
    endgamePoints: 7,
    teleopCount: 61,
    teleopPoints: 61,
    totalCount: 73,
    totalPoints: 73,
    ...overrides,
  };
}

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2026Alliance> = {},
): MatchScoreBreakdown2026Alliance {
  return {
    autoTowerRobot1: TowerRobot2026.LEVEL1,
    autoTowerRobot2: TowerRobot2026.NONE,
    autoTowerRobot3: TowerRobot2026.NONE,
    autoTowerPoints: 6,
    totalAutoPoints: 18,
    hubScore: makeHubScore(),
    endGameTowerRobot1: TowerRobot2026.LEVEL3,
    endGameTowerRobot2: TowerRobot2026.LEVEL2,
    endGameTowerRobot3: TowerRobot2026.LEVEL1,
    endGameTowerPoints: 31,
    totalTowerPoints: 37,
    totalTeleopPoints: 92,
    energizedAchieved: true,
    superchargedAchieved: true,
    traversalAchieved: false,
    minorFoulCount: 2,
    majorFoulCount: 1,
    foulPoints: 9,
    g206Penalty: false,
    adjustPoints: 0,
    totalPoints: 119,
    rp: 5,
    ...overrides,
  };
}

// Cumulative red: Auto 18, Trans 22, Shift 1 32, Shift 2 52, Shift 3 67,
// Shift 4 72, Endgame 119. Cumulative blue: 14, 16, 24, 30, 34, 36, 49.
const scoreBreakdown: MatchScoreBreakdown2026 = {
  red: makeAlliance(),
  blue: makeAlliance({
    autoTowerPoints: 10,
    totalAutoPoints: 14,
    hubScore: makeHubScore({
      transitionPoints: 2,
      shift1Points: 8,
      shift2Points: 6,
      shift3Points: 4,
      shift4Points: 2,
    }),
    totalPoints: 49,
  }),
};

const match: Match = {
  key: '2026test_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 119,
      team_keys: ['frc254', 'frc1114', 'frc2056'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 49,
      team_keys: ['frc148', 'frc217', 'frc33'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2026test',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

// Recharts keeps a hidden offscreen span holding the last measured tick
// string, so look for ticks in the axis itself.
function axisTick(label: string) {
  return screen.getByText(label, { selector: 'tspan' });
}

function renderChart() {
  return render(
    <ScoreByShift2026 scoreBreakdown={scoreBreakdown} match={match} />,
  );
}

describe('ScoreByShift2026', () => {
  test('plots every scoring period on the x axis by default', () => {
    renderChart();

    expect(
      [
        'Auto',
        'Trans',
        'Shift 1',
        'Shift 2',
        'Shift 3',
        'Shift 4',
        'Endgame',
      ].map((period) => axisTick(period).textContent),
    ).toEqual([
      'Auto',
      'Trans',
      'Shift 1',
      'Shift 2',
      'Shift 3',
      'Shift 4',
      'Endgame',
    ]);
  });

  test('labels each point with the cumulative red and blue score', () => {
    renderChart();

    expect(
      [
        '18',
        '22',
        '32',
        '52',
        '67',
        '72',
        '119',
        '14',
        '16',
        '24',
        '30',
        '34',
        '36',
        '49',
      ].map((score) => screen.getByText(score).textContent),
    ).toHaveLength(14);
  });

  test('collapses the chart to the active periods when the toggle is checked', () => {
    renderChart();

    fireEvent.click(
      screen.getByRole('checkbox', { name: 'Active periods only' }),
    );

    expect(
      ['Auto', 'Trans', 'First', 'Second', 'Endgame'].map(
        (period) => axisTick(period).textContent,
      ),
    ).toEqual(['Auto', 'Trans', 'First', 'Second', 'Endgame']);
  });

  test('drops the inactive shift labels when the toggle is checked', () => {
    renderChart();

    fireEvent.click(
      screen.getByRole('checkbox', { name: 'Active periods only' }),
    );

    expect(screen.queryByText('Shift 1', { selector: 'tspan' })).toBeNull();
  });

  test('restores every scoring period when the toggle is unchecked again', () => {
    renderChart();
    const toggle = screen.getByRole('checkbox', {
      name: 'Active periods only',
    });

    fireEvent.click(toggle);
    fireEvent.click(toggle);

    expect(axisTick('Shift 3').textContent).toBe('Shift 3');
  });

  test('names each alliance in the legend by its team numbers', () => {
    renderChart();

    expect([
      screen.getByText('254-1114-2056').textContent,
      screen.getByText('148-217-33').textContent,
    ]).toEqual(['254-1114-2056', '148-217-33']);
  });

  test('places the red label above the blue label when red leads', () => {
    renderChart();

    const red = screen.getByText('119');
    const blue = screen.getByText('49');
    expect(Number(red.getAttribute('y'))).toBeLessThan(
      Number(blue.getAttribute('y')),
    );
  });

  test('places the blue label above the red label when blue leads', () => {
    render(
      <ScoreByShift2026
        scoreBreakdown={{
          red: scoreBreakdown.blue,
          blue: scoreBreakdown.red,
        }}
        match={match}
      />,
    );

    const red = screen.getByText('49');
    const blue = screen.getByText('119');
    expect(Number(blue.getAttribute('y'))).toBeLessThan(
      Number(red.getAttribute('y')),
    );
  });

  test('places the red label above the blue label when the scores are tied', () => {
    render(
      <ScoreByShift2026
        scoreBreakdown={{ red: scoreBreakdown.red, blue: scoreBreakdown.red }}
        match={match}
      />,
    );

    const [red, blue] = screen.getAllByText('119');
    expect(Number(red.getAttribute('y'))).toBeLessThan(
      Number(blue.getAttribute('y')),
    );
  });
});
