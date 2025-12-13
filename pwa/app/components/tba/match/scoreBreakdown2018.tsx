import { Match, MatchScoreBreakdown2018 } from '~/api/tba/read';
import { ConditionalBadge, FoulDisplay } from '~/components/tba/match/common';
import {
  ScoreBreakdownAllianceCell,
  ScoreBreakdownLabelCell,
  ScoreBreakdownRow,
  ScoreBreakdownTable,
} from '~/components/tba/match/scoreBreakdown';
import { Badge } from '~/components/ui/badge';
import {
  ENDGAME_2018_POINTS,
  POINTS_PER_FOUL,
  POINTS_PER_TECH_FOUL,
} from '~/lib/pointValues';

export default function ScoreBreakdown2018({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2018;
  match: Match;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Auto Run */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoRunPoints}
        redValue={scoreBreakdown.red.autoRunPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          <div className="flex flex-row items-center gap-1">
            <div className="flex flex-col items-start justify-center gap-1">
              <ConditionalBadge
                condition={scoreBreakdown.red.autoRobot1 === 'AutoRun'}
                teamKey={match.alliances.red.team_keys[0]}
                alignIcon="left"
              />
              <ConditionalBadge
                condition={scoreBreakdown.red.autoRobot2 === 'AutoRun'}
                teamKey={match.alliances.red.team_keys[1]}
                alignIcon="left"
              />
              <ConditionalBadge
                condition={scoreBreakdown.red.autoRobot3 === 'AutoRun'}
                teamKey={match.alliances.red.team_keys[2]}
                alignIcon="left"
              />
            </div>
            <div className="flex flex-1 justify-center">
              {scoreBreakdown.red.autoRunPoints}
            </div>
          </div>
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">Auto Run</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          <div className="flex flex-row items-center gap-1">
            <div className="flex flex-1 justify-center">
              {scoreBreakdown.blue.autoRunPoints}
            </div>
            <div className="flex flex-col items-end justify-center gap-1">
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoRobot1 === 'AutoRun'}
                teamKey={match.alliances.blue.team_keys[0]}
                alignIcon="right"
              />
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoRobot2 === 'AutoRun'}
                teamKey={match.alliances.blue.team_keys[1]}
                alignIcon="right"
              />
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoRobot3 === 'AutoRun'}
                teamKey={match.alliances.blue.team_keys[2]}
                alignIcon="right"
              />
            </div>
          </div>
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Scale Ownership (sec) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoScaleOwnershipSec}
        redValue={scoreBreakdown.red.autoScaleOwnershipSec}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoScaleOwnershipSec}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Scale Owned
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoScaleOwnershipSec}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Switch Ownership (sec) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoSwitchOwnershipSec}
        redValue={scoreBreakdown.red.autoSwitchOwnershipSec}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoSwitchOwnershipSec}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Switch Owned
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoSwitchOwnershipSec}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Ownership Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoOwnershipPoints}
        redValue={scoreBreakdown.red.autoOwnershipPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.autoOwnershipPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Ownership Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.autoOwnershipPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Auto */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoPoints}
        redValue={scoreBreakdown.red.autoPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.autoPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Auto
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.autoPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Scale Ownership + Boost */}
      <ScoreBreakdownRow
        blueValue={
          (scoreBreakdown.blue.teleopScaleOwnershipSec ?? 0) +
          (scoreBreakdown.blue.teleopScaleBoostSec ?? 0)
        }
        redValue={
          (scoreBreakdown.red.teleopScaleOwnershipSec ?? 0) +
          (scoreBreakdown.red.teleopScaleBoostSec ?? 0)
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopScaleOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.red.teleopScaleBoostSec ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Scale Owned + Boost
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopScaleOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.blue.teleopScaleBoostSec ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Switch Ownership + Boost */}
      <ScoreBreakdownRow
        blueValue={
          (scoreBreakdown.blue.teleopSwitchOwnershipSec ?? 0) +
          (scoreBreakdown.blue.teleopSwitchBoostSec ?? 0)
        }
        redValue={
          (scoreBreakdown.red.teleopSwitchOwnershipSec ?? 0) +
          (scoreBreakdown.red.teleopSwitchBoostSec ?? 0)
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopSwitchOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.red.teleopSwitchBoostSec ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Switch Ownership + Boost
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopSwitchOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.blue.teleopSwitchBoostSec ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Ownership Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.teleopOwnershipPoints}
        redValue={scoreBreakdown.red.teleopOwnershipPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopOwnershipPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Ownership Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopOwnershipPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Force Cubes Total (Played) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultForcePlayed}
        redValue={scoreBreakdown.red.vaultForcePlayed}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.vaultForceTotal} (
          {scoreBreakdown.red.vaultForcePlayed})
        </ScoreBreakdownAllianceCell>

        <ScoreBreakdownLabelCell shade="light">
          Force Cubes Total (Played)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.vaultForceTotal} (
          {scoreBreakdown.blue.vaultForcePlayed})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Levitate Cubes Total (Played) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultLevitatePlayed}
        redValue={scoreBreakdown.red.vaultLevitatePlayed}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.vaultLevitateTotal} (
          {scoreBreakdown.red.vaultLevitatePlayed})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Levitate Cubes Total (Played)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.vaultLevitateTotal} (
          {scoreBreakdown.blue.vaultLevitatePlayed})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Boost Cubes Total (Played) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultBoostPlayed}
        redValue={scoreBreakdown.red.vaultBoostPlayed}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.vaultBoostTotal} (
          {scoreBreakdown.red.vaultBoostPlayed})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Boost Cubes Total (Played)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.vaultBoostTotal} (
          {scoreBreakdown.blue.vaultBoostPlayed})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Vault Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultPoints}
        redValue={scoreBreakdown.red.vaultPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.vaultPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Vault Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.vaultPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 1 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <Badge variant={'outline'}>
            {match.alliances.red.team_keys[0].substring(3)}
          </Badge>
          <span>
            {scoreBreakdown.red.endgameRobot1} (+
            {ENDGAME_2018_POINTS[scoreBreakdown.red.endgameRobot1 ?? 'Unknown']}
            )
          </span>
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          {' '}
          Robot 1 Endgame{' '}
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <Badge variant={'outline'}>
            {match.alliances.blue.team_keys[0].substring(3)}
          </Badge>
          <span>
            {scoreBreakdown.blue.endgameRobot1} (+
            {
              ENDGAME_2018_POINTS[
                scoreBreakdown.blue.endgameRobot1 ?? 'Unknown'
              ]
            }
            )
          </span>
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 2 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <Badge variant={'outline'}>
            {match.alliances.red.team_keys[1].substring(3)}
          </Badge>
          <span>
            {scoreBreakdown.red.endgameRobot2} (+
            {ENDGAME_2018_POINTS[scoreBreakdown.red.endgameRobot2 ?? 'Unknown']}
            )
          </span>
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          {' '}
          Robot 2 Endgame{' '}
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <Badge variant={'outline'}>
            {match.alliances.blue.team_keys[1].substring(3)}
          </Badge>
          <span>
            {scoreBreakdown.blue.endgameRobot2} (+
            {
              ENDGAME_2018_POINTS[
                scoreBreakdown.blue.endgameRobot2 ?? 'Unknown'
              ]
            }
            )
          </span>
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 3 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <Badge variant={'outline'}>
            {match.alliances.red.team_keys[2].substring(3)}
          </Badge>
          <span>
            {scoreBreakdown.red.endgameRobot3} (+
            {ENDGAME_2018_POINTS[scoreBreakdown.red.endgameRobot3 ?? 'Unknown']}
            )
          </span>
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          {' '}
          Robot 3 Endgame{' '}
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <Badge variant={'outline'}>
            {match.alliances.blue.team_keys[2].substring(3)}
          </Badge>
          <span>
            {scoreBreakdown.blue.endgameRobot3} (+
            {
              ENDGAME_2018_POINTS[
                scoreBreakdown.blue.endgameRobot3 ?? 'Unknown'
              ]
            }
            )
          </span>
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Endgame Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.endgamePoints}
        redValue={scoreBreakdown.red.endgamePoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.endgamePoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Endgame Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.endgamePoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Teleop */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.teleopPoints}
        redValue={scoreBreakdown.red.teleopPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Teleop
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Fouls */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.foulPoints}
        redValue={scoreBreakdown.red.foulPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.red.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2018]}
            techFoulsReceived={scoreBreakdown.red.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2018]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Fouls Received
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.blue.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2018]}
            techFoulsReceived={scoreBreakdown.blue.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2018]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Adjustments */}
      {(scoreBreakdown.blue.adjustPoints ?? 0) !== 0 &&
        (scoreBreakdown.red.adjustPoints ?? 0) !== 0 && (
          <ScoreBreakdownRow
            blueValue={scoreBreakdown.blue.adjustPoints}
            redValue={scoreBreakdown.red.adjustPoints}
          >
            <ScoreBreakdownAllianceCell color="red" shade="light">
              {scoreBreakdown.red.adjustPoints}
            </ScoreBreakdownAllianceCell>
            <ScoreBreakdownLabelCell shade="light">
              Adjustments
            </ScoreBreakdownLabelCell>
            <ScoreBreakdownAllianceCell color="blue" shade="light">
              {scoreBreakdown.blue.adjustPoints}
            </ScoreBreakdownAllianceCell>
          </ScoreBreakdownRow>
        )}

      {/* Total Score */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.totalPoints}
        redValue={scoreBreakdown.red.totalPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark" fontWeight="bold">
          {scoreBreakdown.red.totalPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Score
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark" fontWeight="bold">
          {scoreBreakdown.blue.totalPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
  );
}
