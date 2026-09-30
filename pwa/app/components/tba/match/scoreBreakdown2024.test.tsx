import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  AutoLineRobot2024,
  CompLevel,
  EndGameRobot2024,
  type Match,
  type MatchScoreBreakdown2024,
  type MatchScoreBreakdown2024Alliance,
} from '~/api/tba/read';
import ScoreBreakdown2024 from '~/components/tba/match/scoreBreakdown2024';

// The icon-only helpers are swapped for text so each robot's condition is
// visible in the rendered row. The real helpers are covered in common.test.tsx.
vi.mock('~/components/tba/match/common', async (importOriginal) => ({
  ...(await importOriginal<typeof import('~/components/tba/match/common')>()),
  ConditionalCheckmark: ({
    condition,
    teamKey,
  }: {
    condition: boolean;
    teamKey: string;
  }) => (
    // Normalised so these rows don't depend on whether the component passes
    // "frc254" or "254"; which one it should pass is Bug #58, covered by
    // its own failing-test PR.
    <div>
      {teamKey.replace(/^frc/, '')}={condition ? 'yes' : 'no'}
    </div>
  ),
  ConditionalRpAchieved: ({ condition }: { condition: boolean }) => (
    <div>{condition ? 'achieved' : 'missed'}</div>
  ),
}));

function makeAlliance(
  overrides: Partial<MatchScoreBreakdown2024Alliance> = {},
): MatchScoreBreakdown2024Alliance {
  return {
    autoLineRobot1: AutoLineRobot2024.YES,
    autoLineRobot2: AutoLineRobot2024.YES,
    autoLineRobot3: AutoLineRobot2024.NO,
    autoLeavePoints: 4,
    autoAmpNoteCount: 1,
    autoSpeakerNoteCount: 3,
    autoTotalNotePoints: 17,
    autoPoints: 21,
    teleopAmpNoteCount: 4,
    teleopSpeakerNoteAmplifiedCount: 10,
    teleopSpeakerNoteCount: 6,
    teleopTotalNotePoints: 66,
    endGameRobot1: EndGameRobot2024.CENTER_STAGE,
    endGameRobot2: EndGameRobot2024.STAGE_LEFT,
    endGameRobot3: EndGameRobot2024.PARKED,
    trapCenterStage: true,
    trapStageLeft: false,
    trapStageRight: false,
    endGameHarmonyPoints: 2,
    endGameNoteInTrapPoints: 5,
    teleopPoints: 84,
    coopertitionCriteriaMet: true,
    melodyBonusAchieved: true,
    foulCount: 3,
    techFoulCount: 1,
    adjustPoints: 0,
    rp: 3,
    totalPoints: 105,
    ...overrides,
  };
}

function makeBreakdown(
  red: Partial<MatchScoreBreakdown2024Alliance> = {},
  blue: Partial<MatchScoreBreakdown2024Alliance> = {},
): MatchScoreBreakdown2024 {
  return {
    red: makeAlliance(red),
    blue: makeAlliance({
      autoLineRobot1: AutoLineRobot2024.NO,
      autoLineRobot2: AutoLineRobot2024.NO,
      autoLineRobot3: AutoLineRobot2024.YES,
      autoLeavePoints: 2,
      autoAmpNoteCount: 0,
      autoSpeakerNoteCount: 1,
      autoTotalNotePoints: 5,
      autoPoints: 7,
      teleopAmpNoteCount: 2,
      teleopSpeakerNoteAmplifiedCount: 3,
      teleopSpeakerNoteCount: 8,
      teleopTotalNotePoints: 34,
      endGameRobot1: EndGameRobot2024.STAGE_RIGHT,
      endGameRobot2: EndGameRobot2024.NONE,
      endGameRobot3: undefined,
      trapCenterStage: false,
      trapStageLeft: false,
      trapStageRight: true,
      endGameHarmonyPoints: 0,
      endGameNoteInTrapPoints: 5,
      teleopPoints: 47,
      coopertitionCriteriaMet: false,
      melodyBonusAchieved: false,
      foulCount: undefined,
      techFoulCount: undefined,
      adjustPoints: 0,
      rp: 0,
      totalPoints: 54,
      ...blue,
    }),
  };
}

const match: Match = {
  key: '2024test_qm1',
  comp_level: CompLevel.QM,
  set_number: 1,
  match_number: 1,
  alliances: {
    red: {
      score: 105,
      team_keys: ['frc254', 'frc1114', 'frc2056'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
    blue: {
      score: 54,
      team_keys: ['frc148', 'frc217', 'frc33'],
      surrogate_team_keys: [],
      dq_team_keys: [],
    },
  },
  winning_alliance: AllianceColor.RED,
  event_key: '2024test',
  time: null,
  actual_time: null,
  predicted_time: null,
  post_result_time: null,
  score_breakdown: null,
  videos: [],
};

function renderBreakdown(scoreBreakdown = makeBreakdown()) {
  return render(
    <ScoreBreakdown2024 scoreBreakdown={scoreBreakdown} match={match} />,
  );
}

describe('ScoreBreakdown2024', () => {
  test('shows each robot auto leave result', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: '254=yes 1114=yes 2056=no (+4) Auto Leave 148=no 217=no 33=yes (+2)',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Auto Amp Note Count', red: '1', blue: '0' },
    { label: 'Auto Speaker Note Count', red: '3', blue: '1' },
    { label: 'Auto Note Points', red: '17', blue: '5' },
    { label: 'Total Auto', red: '21', blue: '7' },
    { label: 'Teleop Amp Note Count', red: '4', blue: '2' },
    { label: 'Teleop Note Points', red: '66', blue: '34' },
    { label: 'Harmony Points', red: '2', blue: '0' },
    { label: 'Trap Points', red: '5', blue: '5' },
    { label: 'Total Teleop', red: '84', blue: '47' },
    { label: 'Adjustments', red: '0', blue: '0' },
    { label: 'Total Score', red: '105', blue: '54' },
    { label: 'RP', red: '+3 RP', blue: '+0 RP' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test('shows amplified and regular teleop speaker note counts', () => {
    renderBreakdown();

    expect(
      screen.getByRole('row', {
        name: '10 6 Teleop Speaker Note Count 3 8',
      }),
    ).toBeTruthy();
  });

  // Wrong today: EndgameRobotCell labels an onstage robot "Spotlit (+4)"
  // when the TRAP at its stage position holds a note, and never reads the
  // microphone flags.
  // Correct: spotlit comes from a HIGH NOTE on the MICROPHONE above the robot
  // (micCenterStage / micStageLeft / micStageRight); a trap note is a separate
  // 5-point alliance score. 2024 Game Manual (CRESCENDO), Section 6.5.4
  // SPOTLIGHTING (page 47, section revision V10): "ONSTAGE ROBOTS paired with
  // (i.e. below) the MICROPHONE on which the HIGH NOTE was scored are awarded
  // a greater number of points per Table 6-2"; Table 6-2 (page 48): ONSTAGE
  // (not SPOTLIT) 3, ONSTAGE (SPOTLIT) 4, NOTE in TRAP 5. Latest published
  // manual (PDF last modified 2024-04-09, after all Team Updates):
  // https://firstfrc.blob.core.windows.net/frc2024/Manual/2024GameManual.pdf
  const noStageFlags = {
    trapCenterStage: false,
    trapStageLeft: false,
    trapStageRight: false,
    micCenterStage: false,
    micStageLeft: false,
    micStageRight: false,
  };

  test('Bug #57: a trap note alone does not make an onstage robot spotlit', () => {
    renderBreakdown(
      makeBreakdown(
        {
          endGameRobot1: EndGameRobot2024.CENTER_STAGE,
          ...noStageFlags,
          trapCenterStage: true,
        },
        { endGameRobot1: EndGameRobot2024.NONE, ...noStageFlags },
      ),
    );

    expect(
      screen.getByRole('row', {
        name: '254 Onstage (+3) Robot 1 Endgame 148 None (+0)',
      }),
    ).toBeTruthy();
  });

  test.each([
    {
      position: 'center stage',
      endgame: EndGameRobot2024.CENTER_STAGE,
      mic: { micCenterStage: true },
    },
    {
      position: 'stage left',
      endgame: EndGameRobot2024.STAGE_LEFT,
      mic: { micStageLeft: true },
    },
    {
      position: 'stage right',
      endgame: EndGameRobot2024.STAGE_RIGHT,
      mic: { micStageRight: true },
    },
  ])(
    'Bug #57: a high note on the microphone above an onstage robot at $position makes it spotlit',
    ({ endgame, mic }) => {
      renderBreakdown(
        makeBreakdown(
          { endGameRobot1: endgame, ...noStageFlags, ...mic },
          { endGameRobot1: EndGameRobot2024.NONE, ...noStageFlags },
        ),
      );

      expect(
        screen.getByRole('row', {
          name: '254 Spotlit (+4) Robot 1 Endgame 148 None (+0)',
        }),
      ).toBeTruthy();
    },
  );

  test.each([
    { name: '1114 Onstage (+3) Robot 2 Endgame 217 None (+0)' },
    { name: '2056 Parked (+1) Robot 3 Endgame 33 None (+0)' },
  ])('shows the stage state and points in row "$name"', ({ name }) => {
    renderBreakdown();

    expect(screen.getByRole('row', { name })).toBeTruthy();
  });

  test('treats missing trap flags as no trap note', () => {
    renderBreakdown(
      makeBreakdown(
        {
          trapCenterStage: undefined,
          trapStageLeft: undefined,
          trapStageRight: undefined,
        },
        {
          trapCenterStage: undefined,
          trapStageLeft: undefined,
          trapStageRight: undefined,
        },
      ),
    );

    expect(
      screen.getByRole('row', {
        name: '254 Onstage (+3) Robot 1 Endgame 148 Onstage (+3)',
      }),
    ).toBeTruthy();
  });

  test.each([
    { label: 'Coopertition Criteria Met', red: 'achieved', blue: 'missed' },
    { label: 'Melody Bonus', red: 'achieved', blue: 'missed' },
  ])('shows $label for both alliances', ({ label, red, blue }) => {
    renderBreakdown();

    expect(
      screen.getByRole('row', { name: `${red} ${label} ${blue}` }),
    ).toBeTruthy();
  });

  test('treats missing bonus flags as not achieved', () => {
    renderBreakdown(
      makeBreakdown(
        { coopertitionCriteriaMet: undefined, melodyBonusAchieved: undefined },
        { coopertitionCriteriaMet: undefined, melodyBonusAchieved: undefined },
      ),
    );

    expect(
      screen.getAllByRole('row', { name: /^missed .* missed$/ }),
    ).toHaveLength(2);
  });

  // Both alliances get identical counts in these two tests: which
  // alliance's counts belong under which column is Bug #56, covered by its
  // own failing-test PR.
  test('shows foul counts with points', () => {
    renderBreakdown(
      makeBreakdown(
        { foulCount: 3, techFoulCount: 1 },
        { foulCount: 3, techFoulCount: 1 },
      ),
    );

    expect(
      screen.getByRole('row', {
        name: '3 (+6) / 1 (+5) Fouls / Tech Fouls 3 (+6) / 1 (+5)',
      }),
    ).toBeTruthy();
  });

  test('shows blank foul counts when missing', () => {
    renderBreakdown(
      makeBreakdown(
        { foulCount: undefined, techFoulCount: undefined },
        { foulCount: undefined, techFoulCount: undefined },
      ),
    );

    expect(
      screen.getByRole('row', {
        name: '(+0) / (+0) Fouls / Tech Fouls (+0) / (+0)',
      }),
    ).toBeTruthy();
  });
});
