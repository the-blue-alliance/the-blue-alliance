import { Match, MatchScoreBreakdown2018 } from '~/api/tba/read';
import { ConditionalBadge } from '~/components/tba/match/common';
import {
  ScoreBreakdownBlueCell,
  ScoreBreakdownLabelCell,
  ScoreBreakdownRedCell,
  ScoreBreakdownRow,
  ScoreBreakdownTable,
} from '~/components/tba/match/scoreBreakdown';

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
        <ScoreBreakdownRedCell shade="light">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-center gap-1">
              <ConditionalBadge
                condition={scoreBreakdown.red.autoRobot1 === 'AutoRun'}
                teamKey={match.alliances.red.team_keys[0]}
              />
              <ConditionalBadge
                condition={scoreBreakdown.red.autoRobot2 === 'AutoRun'}
                teamKey={match.alliances.red.team_keys[1]}
              />
              <ConditionalBadge
                condition={scoreBreakdown.red.autoRobot3 === 'AutoRun'}
                teamKey={match.alliances.red.team_keys[2]}
              />
            </div>
            <div className="flex justify-center">
              {scoreBreakdown.red.autoRunPoints}
            </div>
          </div>
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Run
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          <div className="flex flex-col gap-1">
            <div className="flex items-center justify-center gap-1">
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoRobot1 === 'AutoRun'}
                teamKey={match.alliances.blue.team_keys[0]}
              />
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoRobot2 === 'AutoRun'}
                teamKey={match.alliances.blue.team_keys[1]}
              />
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoRobot3 === 'AutoRun'}
                teamKey={match.alliances.blue.team_keys[2]}
              />
            </div>
            <div className="flex justify-center">
              {scoreBreakdown.blue.autoRunPoints}
            </div>
          </div>
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Auto Scale Ownership (sec) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoScaleOwnershipSec}
        redValue={scoreBreakdown.red.autoScaleOwnershipSec}
      >
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.autoScaleOwnershipSec}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Scale Ownership (sec)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.autoScaleOwnershipSec}
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Auto Switch Ownership (sec) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoSwitchOwnershipSec}
        redValue={scoreBreakdown.red.autoSwitchOwnershipSec}
      >
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.autoSwitchOwnershipSec}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Switch Ownership (sec)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.autoSwitchOwnershipSec}
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Ownership Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoOwnershipPoints}
        redValue={scoreBreakdown.red.autoOwnershipPoints}
      >
        <ScoreBreakdownRedCell shade="dark">
          {scoreBreakdown.red.autoOwnershipPoints}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="dark">
          Ownership Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="dark">
          {scoreBreakdown.blue.autoOwnershipPoints}
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Total Auto */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoPoints}
        redValue={scoreBreakdown.red.autoPoints}
      >
        <ScoreBreakdownRedCell shade="dark">
          {scoreBreakdown.red.autoPoints}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Auto
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="dark">
          {scoreBreakdown.blue.autoPoints}
        </ScoreBreakdownBlueCell>
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
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.teleopScaleOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.red.teleopScaleBoostSec ?? 0}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Scale Ownership + Boost
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.teleopScaleOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.blue.teleopScaleBoostSec ?? 0}
        </ScoreBreakdownBlueCell>
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
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.teleopSwitchOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.red.teleopSwitchBoostSec ?? 0}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Switch Ownership + Boost
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.teleopSwitchOwnershipSec ?? 0} +{' '}
          {scoreBreakdown.blue.teleopSwitchBoostSec ?? 0}
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Ownership Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.teleopOwnershipPoints}
        redValue={scoreBreakdown.red.teleopOwnershipPoints}
      >
        <ScoreBreakdownRedCell shade="dark">
          {scoreBreakdown.red.teleopOwnershipPoints}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="dark">
          Ownership Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="dark">
          {scoreBreakdown.blue.teleopOwnershipPoints}
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Force Cubes Total (Played) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultForcePlayed}
        redValue={scoreBreakdown.red.vaultForcePlayed}
      >
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.vaultForceTotal} (
          {scoreBreakdown.red.vaultForcePlayed})
        </ScoreBreakdownRedCell>

        <ScoreBreakdownLabelCell shade="light">
          Force Cubes Total (Played)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.vaultForceTotal} (
          {scoreBreakdown.blue.vaultForcePlayed})
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Levitate Cubes Total (Played) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultLevitatePlayed}
        redValue={scoreBreakdown.red.vaultLevitatePlayed}
      >
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.vaultLevitateTotal} (
          {scoreBreakdown.red.vaultLevitatePlayed})
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Levitate Cubes Total (Played)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.vaultLevitateTotal} (
          {scoreBreakdown.blue.vaultLevitatePlayed})
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Boost Cubes Total (Played) */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultBoostPlayed}
        redValue={scoreBreakdown.red.vaultBoostPlayed}
      >
        <ScoreBreakdownRedCell shade="light">
          {scoreBreakdown.red.vaultBoostTotal} (
          {scoreBreakdown.red.vaultBoostPlayed})
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="light">
          Boost Cubes Total (Played)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="light">
          {scoreBreakdown.blue.vaultBoostTotal} (
          {scoreBreakdown.blue.vaultBoostPlayed})
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>

      {/* Vault Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.vaultPoints}
        redValue={scoreBreakdown.red.vaultPoints}
      >
        <ScoreBreakdownRedCell shade="dark">
          {scoreBreakdown.red.vaultPoints}
        </ScoreBreakdownRedCell>
        <ScoreBreakdownLabelCell shade="dark">
          Vault Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownBlueCell shade="dark">
          {scoreBreakdown.blue.vaultPoints}
        </ScoreBreakdownBlueCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
  );
}
