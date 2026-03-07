import { Match, MatchScoreBreakdown2026, TowerRobot2026 } from '~/api/tba/read';
import {
  ConditionalBadge,
  ConditionalRpAchieved,
} from '~/components/tba/match/common';
import {
  ScoreBreakdownAllianceCell,
  ScoreBreakdownLabelCell,
  ScoreBreakdownRow,
  ScoreBreakdownTable,
} from '~/components/tba/match/scoreBreakdown';
import { Badge } from '~/components/ui/badge';

const TOWER_ROBOT_POINTS: Record<TowerRobot2026, number> = {
  Level3: 15,
  Level2: 10,
  Level1: 6,
  None: 0,
};

const TOWER_ROBOT_DISPLAY: Record<TowerRobot2026, string> = {
  Level3: 'Level 3',
  Level2: 'Level 2',
  Level1: 'Level 1',
  None: 'None',
};

function EndgameTowerCell({
  endgame,
  teamKey,
}: {
  endgame: TowerRobot2026;
  teamKey: string;
}) {
  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant="outline">{teamKey.substring(3)}</Badge>
      <span>
        {TOWER_ROBOT_DISPLAY[endgame]} (+{TOWER_ROBOT_POINTS[endgame]})
      </span>
    </div>
  );
}

export default function ScoreBreakdown2026({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2026;
  match: Match;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Auto Tower */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoTowerPoints}
        redValue={scoreBreakdown.red.autoTowerPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          <div className="flex flex-row items-center gap-1">
            <div className="flex flex-col items-start justify-center gap-1">
              <ConditionalBadge
                condition={scoreBreakdown.red.autoTowerRobot1 !== 'None'}
                teamKey={match.alliances.red.team_keys[0]}
                alignIcon="left"
              />
              <ConditionalBadge
                condition={scoreBreakdown.red.autoTowerRobot2 !== 'None'}
                teamKey={match.alliances.red.team_keys[1]}
                alignIcon="left"
              />
              <ConditionalBadge
                condition={scoreBreakdown.red.autoTowerRobot3 !== 'None'}
                teamKey={match.alliances.red.team_keys[2]}
                alignIcon="left"
              />
            </div>
            <div className="flex flex-1 justify-center">
              {scoreBreakdown.red.autoTowerPoints}
            </div>
          </div>
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Auto Tower
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          <div className="flex flex-row items-center gap-1">
            <div className="flex flex-1 justify-center">
              {scoreBreakdown.blue.autoTowerPoints}
            </div>
            <div className="flex flex-col items-end justify-center gap-1">
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoTowerRobot1 !== 'None'}
                teamKey={match.alliances.blue.team_keys[0]}
                alignIcon="right"
              />
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoTowerRobot2 !== 'None'}
                teamKey={match.alliances.blue.team_keys[1]}
                alignIcon="right"
              />
              <ConditionalBadge
                condition={scoreBreakdown.blue.autoTowerRobot3 !== 'None'}
                teamKey={match.alliances.blue.team_keys[2]}
                alignIcon="right"
              />
            </div>
          </div>
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Auto */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.totalAutoPoints}
        redValue={scoreBreakdown.red.totalAutoPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.totalAutoPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Auto
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.totalAutoPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Hub Score: Shift Counts */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.hubScore.shift1Count}
        redValue={scoreBreakdown.red.hubScore.shift1Count}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.hubScore.shift1Count}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Shift 1 Count
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.hubScore.shift1Count}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.hubScore.shift2Count}
        redValue={scoreBreakdown.red.hubScore.shift2Count}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.hubScore.shift2Count}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Shift 2 Count
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.hubScore.shift2Count}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.hubScore.shift3Count}
        redValue={scoreBreakdown.red.hubScore.shift3Count}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.hubScore.shift3Count}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Shift 3 Count
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.hubScore.shift3Count}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.hubScore.shift4Count}
        redValue={scoreBreakdown.red.hubScore.shift4Count}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.hubScore.shift4Count}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Shift 4 Count
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.hubScore.shift4Count}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Shift Points */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.hubScore.shift1Points +
          scoreBreakdown.blue.hubScore.shift2Points +
          scoreBreakdown.blue.hubScore.shift3Points +
          scoreBreakdown.blue.hubScore.shift4Points
        }
        redValue={
          scoreBreakdown.red.hubScore.shift1Points +
          scoreBreakdown.red.hubScore.shift2Points +
          scoreBreakdown.red.hubScore.shift3Points +
          scoreBreakdown.red.hubScore.shift4Points
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.hubScore.shift1Points} /{' '}
          {scoreBreakdown.red.hubScore.shift2Points} /{' '}
          {scoreBreakdown.red.hubScore.shift3Points} /{' '}
          {scoreBreakdown.red.hubScore.shift4Points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Shift Points (1/2/3/4)
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.hubScore.shift1Points} /{' '}
          {scoreBreakdown.blue.hubScore.shift2Points} /{' '}
          {scoreBreakdown.blue.hubScore.shift3Points} /{' '}
          {scoreBreakdown.blue.hubScore.shift4Points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Count */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.hubScore.teleopCount}
        redValue={scoreBreakdown.red.hubScore.teleopCount}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.hubScore.teleopCount}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Count
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.hubScore.teleopCount}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Hub Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.hubScore.teleopPoints}
        redValue={scoreBreakdown.red.hubScore.teleopPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.hubScore.teleopPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Teleop Hub Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.hubScore.teleopPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 1 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <EndgameTowerCell
            endgame={scoreBreakdown.red.endGameTowerRobot1}
            teamKey={match.alliances.red.team_keys[0]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot 1 Endgame
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <EndgameTowerCell
            endgame={scoreBreakdown.blue.endGameTowerRobot1}
            teamKey={match.alliances.blue.team_keys[0]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 2 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <EndgameTowerCell
            endgame={scoreBreakdown.red.endGameTowerRobot2}
            teamKey={match.alliances.red.team_keys[1]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot 2 Endgame
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <EndgameTowerCell
            endgame={scoreBreakdown.blue.endGameTowerRobot2}
            teamKey={match.alliances.blue.team_keys[1]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 3 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <EndgameTowerCell
            endgame={scoreBreakdown.red.endGameTowerRobot3}
            teamKey={match.alliances.red.team_keys[2]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot 3 Endgame
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="light"
          className="flex flex-col items-center gap-1"
        >
          <EndgameTowerCell
            endgame={scoreBreakdown.blue.endGameTowerRobot3}
            teamKey={match.alliances.blue.team_keys[2]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Endgame Tower Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.endGameTowerPoints}
        redValue={scoreBreakdown.red.endGameTowerPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.endGameTowerPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Endgame Tower Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.endGameTowerPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Tower Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.totalTowerPoints}
        redValue={scoreBreakdown.red.totalTowerPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.totalTowerPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Tower Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.totalTowerPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Teleop */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.totalTeleopPoints}
        redValue={scoreBreakdown.red.totalTeleopPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.totalTeleopPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Teleop
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.totalTeleopPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Energized Bonus */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.energizedAchieved}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Energized Bonus
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.energizedAchieved}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Supercharged Bonus */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.superchargedAchieved}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Supercharged Bonus
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.superchargedAchieved}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Traversal Bonus */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.traversalAchieved}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Traversal Bonus
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.traversalAchieved}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Fouls / Major Fouls */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.minorFoulCount} /{' '}
          {scoreBreakdown.red.majorFoulCount}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Fouls / Major Fouls
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.minorFoulCount} /{' '}
          {scoreBreakdown.blue.majorFoulCount}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Foul Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.foulPoints}
        redValue={scoreBreakdown.red.foulPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.foulPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Foul Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.foulPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Adjustments */}
      {((scoreBreakdown.blue.adjustPoints ?? 0) !== 0 ||
        (scoreBreakdown.red.adjustPoints ?? 0) !== 0) && (
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

      {/* Ranking Points */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          +{scoreBreakdown.red.rp} RP
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">RP</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          +{scoreBreakdown.blue.rp} RP
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
  );
}
