import { Match, MatchScoreBreakdown2019 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import {
  ScoreBreakdownAllianceCell,
  ScoreBreakdownLabelCell,
  ScoreBreakdownRow,
  ScoreBreakdownTable,
} from '~/components/tba/match/scoreBreakdown';
import { Badge } from '~/components/ui/badge';
import { POINTS_PER_FOUL, POINTS_PER_TECH_FOUL } from '~/lib/pointValues';

const ENDGAME_2019_POINTS: Record<string, number> = {
  HabLevel3: 6,
  HabLevel2: 3,
  HabLevel1: 3,
  None: 0,
  Unknown: 0,
};

export default function ScoreBreakdown2019({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2019;
  match: Match;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Sandstorm / HAB Line */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.sandStormBonusPoints}
        blueValue={scoreBreakdown.blue.sandStormBonusPoints}
      >
        <ScoreBreakdownAllianceCell
          color="red"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={
              scoreBreakdown.red.habLineRobot1 === 'CrossedHabLineInSandstorm'
            }
            teamKey={match.alliances.red.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.red.habLineRobot2 === 'CrossedHabLineInSandstorm'
            }
            teamKey={match.alliances.red.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.red.habLineRobot3 === 'CrossedHabLineInSandstorm'
            }
            teamKey={match.alliances.red.team_keys[2]}
          />
          (+{scoreBreakdown.red.sandStormBonusPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Sandstorm Bonus
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={
              scoreBreakdown.blue.habLineRobot1 ===
              'CrossedHabLineInSandstorm'
            }
            teamKey={match.alliances.blue.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.blue.habLineRobot2 ===
              'CrossedHabLineInSandstorm'
            }
            teamKey={match.alliances.blue.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.blue.habLineRobot3 ===
              'CrossedHabLineInSandstorm'
            }
            teamKey={match.alliances.blue.team_keys[2]}
          />
          (+{scoreBreakdown.blue.sandStormBonusPoints})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Hatch Panel Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.hatchPanelPoints}
        blueValue={scoreBreakdown.blue.hatchPanelPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.hatchPanelPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Hatch Panel Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.hatchPanelPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Cargo Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.cargoPoints}
        blueValue={scoreBreakdown.blue.cargoPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.cargoPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Cargo Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.cargoPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 1 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <EndgameRobotCell
            endgame={scoreBreakdown.red.endgameRobot1}
            teamKey={match.alliances.red.team_keys[0]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot 1 Endgame
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <EndgameRobotCell
            endgame={scoreBreakdown.blue.endgameRobot1}
            teamKey={match.alliances.blue.team_keys[0]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 2 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <EndgameRobotCell
            endgame={scoreBreakdown.red.endgameRobot2}
            teamKey={match.alliances.red.team_keys[1]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot 2 Endgame
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <EndgameRobotCell
            endgame={scoreBreakdown.blue.endgameRobot2}
            teamKey={match.alliances.blue.team_keys[1]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Robot 3 Endgame */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <EndgameRobotCell
            endgame={scoreBreakdown.red.endgameRobot3}
            teamKey={match.alliances.red.team_keys[2]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot 3 Endgame
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <EndgameRobotCell
            endgame={scoreBreakdown.blue.endgameRobot3}
            teamKey={match.alliances.blue.team_keys[2]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* HAB Climb Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.habClimbPoints}
        blueValue={scoreBreakdown.blue.habClimbPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.habClimbPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          HAB Climb Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.habClimbPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Teleop */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopPoints}
        blueValue={scoreBreakdown.blue.teleopPoints}
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

      {/* Complete Rocket RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.completeRocketRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Complete Rocket
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.completeRocketRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* HAB Docking RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.habDockingRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          HAB Docking
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.habDockingRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Fouls / Tech Fouls */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.foulPoints}
        blueValue={scoreBreakdown.blue.foulPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.red.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2019]}
            techFoulsReceived={scoreBreakdown.red.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2019]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Fouls / Tech Fouls
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.blue.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2019]}
            techFoulsReceived={scoreBreakdown.blue.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2019]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Adjustments */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.adjustPoints ?? 0}
        blueValue={scoreBreakdown.blue.adjustPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.adjustPoints ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Adjustments
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.adjustPoints ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Score */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.totalPoints}
        blueValue={scoreBreakdown.blue.totalPoints}
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

      {/* RP */}
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

function EndgameRobotCell({
  endgame,
  teamKey,
}: {
  endgame: MatchScoreBreakdown2019['red']['endgameRobot1'];
  teamKey: string;
}) {
  const points = ENDGAME_2019_POINTS[endgame] ?? 0;
  const displayMap: Record<string, string> = {
    HabLevel3: 'HAB 3',
    HabLevel2: 'HAB 2',
    HabLevel1: 'HAB 1',
    None: 'None',
    Unknown: 'Unknown',
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant="outline">{teamKey.substring(3)}</Badge>
      {displayMap[endgame] ?? endgame} (+{points})
    </div>
  );
}
