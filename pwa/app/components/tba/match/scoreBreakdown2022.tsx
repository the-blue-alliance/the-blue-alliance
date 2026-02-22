import { Match, MatchScoreBreakdown2022 } from '~/api/tba/read';
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

export default function ScoreBreakdown2022({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2022;
  match: Match;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Taxi */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoTaxiPoints}
        blueValue={scoreBreakdown.blue.autoTaxiPoints}
      >
        <ScoreBreakdownAllianceCell
          color="red"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={scoreBreakdown.red.taxiRobot1 === 'Yes'}
            teamKey={match.alliances.red.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.red.taxiRobot2 === 'Yes'}
            teamKey={match.alliances.red.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.red.taxiRobot3 === 'Yes'}
            teamKey={match.alliances.red.team_keys[2]}
          />
          (+{scoreBreakdown.red.autoTaxiPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">Taxi</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.taxiRobot1 === 'Yes'}
            teamKey={match.alliances.blue.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.taxiRobot2 === 'Yes'}
            teamKey={match.alliances.blue.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.taxiRobot3 === 'Yes'}
            teamKey={match.alliances.blue.team_keys[2]}
          />
          (+{scoreBreakdown.blue.autoTaxiPoints})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Cargo Lower */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCargoLowerNear ?? 0}
        blueValue={scoreBreakdown.blue.autoCargoLowerNear ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoCargoLowerNear ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Cargo Lower Hub
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoCargoLowerNear ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Cargo Upper */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCargoUpperNear ?? 0}
        blueValue={scoreBreakdown.blue.autoCargoUpperNear ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoCargoUpperNear ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Cargo Upper Hub
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoCargoUpperNear ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Cargo Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCargoPoints}
        blueValue={scoreBreakdown.blue.autoCargoPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.autoCargoPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Auto Cargo Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.autoCargoPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Auto */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoPoints}
        blueValue={scoreBreakdown.blue.autoPoints}
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

      {/* Teleop Cargo Lower */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCargoLowerNear ?? 0}
        blueValue={scoreBreakdown.blue.teleopCargoLowerNear ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopCargoLowerNear ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Cargo Lower Hub
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopCargoLowerNear ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Cargo Upper */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCargoUpperNear ?? 0}
        blueValue={scoreBreakdown.blue.teleopCargoUpperNear ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopCargoUpperNear ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Cargo Upper Hub
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopCargoUpperNear ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Cargo Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCargoPoints}
        blueValue={scoreBreakdown.blue.teleopCargoPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopCargoPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Teleop Cargo Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopCargoPoints}
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

      {/* Endgame Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.endgamePoints}
        blueValue={scoreBreakdown.blue.endgamePoints}
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

      {/* Quintet Achieved */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.quintetAchieved ?? false}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Quintet Achieved
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.quintetAchieved ?? false}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Cargo Bonus RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.cargoBonusRankingPoint ?? false}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Cargo Bonus RP
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.cargoBonusRankingPoint ?? false}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Hangar Bonus RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.hangarBonusRankingPoint ?? false}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Hangar Bonus RP
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.hangarBonusRankingPoint ?? false}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Fouls */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.foulPoints}
        blueValue={scoreBreakdown.blue.foulPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.blue.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2022]}
            techFoulsReceived={scoreBreakdown.blue.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2022]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">Fouls</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.red.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2022]}
            techFoulsReceived={scoreBreakdown.red.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2022]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Adjustments */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.adjustPoints}
        blueValue={scoreBreakdown.blue.adjustPoints}
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
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.rp ?? undefined}
        blueValue={scoreBreakdown.blue.rp ?? undefined}
      >
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
  endgame: MatchScoreBreakdown2022['red']['endgameRobot1'];
  teamKey: string;
}) {
  const pointMap: Record<string, number> = {
    Traversal: 15,
    High: 10,
    Mid: 6,
    Low: 4,
    None: 0,
  };

  const display = endgame ?? 'None';
  const points = pointMap[display] ?? 0;

  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant="outline">{teamKey.substring(3)}</Badge>
      {display} (+{points})
    </div>
  );
}
