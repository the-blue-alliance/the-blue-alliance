import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  type Match,
  PlayoffType,
} from '~/api/tba/read';
import BracketViewThroughSelect, {
  matchesViewedThrough,
} from '~/components/tba/bracketViewThroughSelect';
import {
  makeMatch as baseMatch,
  makeAlliance,
  makeEvent,
} from '~/test/factories';

function makeMatch(setNumber: number): Match {
  return baseMatch({
    key: `2026test_sf${setNumber}m1`,
    comp_level: CompLevel.SF,
    set_number: setNumber,
    alliances: {
      red: makeAlliance(-1, []),
      blue: makeAlliance(-1, []),
    },
    winning_alliance: AllianceColor.NO_ALLIANCE,
  });
}

const event = makeEvent({
  playoff_type: PlayoffType.DOUBLE_ELIM_8_TEAM,
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe('matchesViewedThrough', () => {
  test('keeps matches up to and including the chosen match', () => {
    const matches = [makeMatch(1), makeMatch(2), makeMatch(3)];

    expect(matchesViewedThrough(matches, '2').map((m) => m.set_number)).toEqual(
      [1, 2],
    );
  });

  test('keeps every match when viewing all matches', () => {
    const matches = [makeMatch(1), makeMatch(2)];

    expect(matchesViewedThrough(matches, 'all')).toHaveLength(2);
  });
});

describe('BracketViewThroughSelect', () => {
  test('shows the select outside production', () => {
    render(
      <BracketViewThroughSelect
        matches={[makeMatch(1)]}
        event={event}
        value="all"
        onValueChange={() => {}}
      />,
    );

    expect(screen.getByLabelText('View from Match')).toBeTruthy();
  });

  test('hides the select in production', () => {
    vi.stubEnv('PROD', true);

    render(
      <BracketViewThroughSelect
        matches={[makeMatch(1)]}
        event={event}
        value="all"
        onValueChange={() => {}}
      />,
    );

    expect(screen.queryByLabelText('View from Match')).toBeNull();
  });
});
