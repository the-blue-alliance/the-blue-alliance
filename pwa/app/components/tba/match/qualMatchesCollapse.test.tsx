import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { AllianceColor, CompLevel, type Match } from '~/api/tba/read';
import QualMatchesCollapse from '~/components/tba/match/qualMatchesCollapse';

function makeMatch(key: string, redScore: number, blueScore: number): Match {
  return {
    key,
    comp_level: CompLevel.QM,
    set_number: 1,
    match_number: 1,
    alliances: {
      red: {
        score: redScore,
        team_keys: ['frc254', 'frc1114', 'frc2056'],
        surrogate_team_keys: [],
        dq_team_keys: [],
      },
      blue: {
        score: blueScore,
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
}

describe('QualMatchesCollapse', () => {
  test('offers to show matches when every qual is played', () => {
    render(
      <QualMatchesCollapse
        hasElims
        matches={[
          makeMatch('2026test_qm1', 94, 43),
          makeMatch('2026test_qm2', 50, 60),
        ]}
      >
        <p>Quals 1</p>
      </QualMatchesCollapse>,
    );

    expect(
      screen
        .getByRole('button', { name: 'Show all 2 qualification matches' })
        .getAttribute('aria-expanded'),
    ).toBe('false');
  });

  test('omits the toggle while a qual is unplayed', () => {
    render(
      <QualMatchesCollapse
        hasElims
        matches={[
          makeMatch('2026test_qm1', 94, 43),
          makeMatch('2026test_qm2', -1, -1),
        ]}
      >
        <p>Quals 1</p>
      </QualMatchesCollapse>,
    );

    expect(screen.queryByRole('button')).toBeNull();
  });

  test('marks matches expanded after clicking show', () => {
    render(
      <QualMatchesCollapse
        hasElims
        matches={[
          makeMatch('2026test_qm1', 94, 43),
          makeMatch('2026test_qm2', 50, 60),
        ]}
      >
        <p>Quals 1</p>
      </QualMatchesCollapse>,
    );

    fireEvent.click(
      screen.getByRole('button', { name: 'Show all 2 qualification matches' }),
    );

    expect(
      screen
        .getByRole('button', { name: 'Hide qualification matches' })
        .getAttribute('aria-expanded'),
    ).toBe('true');
  });

  test('omits the toggle before any elim match exists', () => {
    render(
      <QualMatchesCollapse
        hasElims={false}
        matches={[
          makeMatch('2026test_qm1', 94, 43),
          makeMatch('2026test_qm2', 50, 60),
        ]}
      >
        <p>Quals 1</p>
      </QualMatchesCollapse>,
    );

    expect(screen.queryByRole('button')).toBeNull();
  });
});
