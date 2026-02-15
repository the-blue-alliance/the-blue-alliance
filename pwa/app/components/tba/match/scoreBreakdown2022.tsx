import { Match, MatchScoreBreakdown2022 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';

export default function ScoreBreakdown2022({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2022;
  match: Match;
}) {
  return (
    <Table className="table-fixed overflow-hidden rounded-lg text-center">
      <colgroup>
        <col />
        <col className="w-[45%]" />
        <col />
      </colgroup>
      <TableBody>
        {/* Taxi */}
        <TableRow>
          <TableCell
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.red.taxiRobot1 === 'Yes'}
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.taxiRobot2 === 'Yes'}
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.taxiRobot3 === 'Yes'}
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.red.autoTaxiPoints})
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Taxi
          </TableCell>
          <TableCell
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.taxiRobot1 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.taxiRobot2 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.taxiRobot3 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.blue.autoTaxiPoints})
          </TableCell>
        </TableRow>

        {/* Auto Cargo Lower */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoCargoLowerNear ?? 0}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Cargo Lower Hub
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoCargoLowerNear ?? 0}
          </TableCell>
        </TableRow>

        {/* Auto Cargo Upper */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoCargoUpperNear ?? 0}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Cargo Upper Hub
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoCargoUpperNear ?? 0}
          </TableCell>
        </TableRow>

        {/* Auto Cargo Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoCargoPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Auto Cargo Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoCargoPoints}
          </TableCell>
        </TableRow>

        {/* Total Auto */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Total Auto
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoPoints}
          </TableCell>
        </TableRow>

        {/* Teleop Cargo Lower */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopCargoLowerNear ?? 0}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Cargo Lower Hub
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopCargoLowerNear ?? 0}
          </TableCell>
        </TableRow>

        {/* Teleop Cargo Upper */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopCargoUpperNear ?? 0}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Cargo Upper Hub
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopCargoUpperNear ?? 0}
          </TableCell>
        </TableRow>

        {/* Teleop Cargo Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopCargoPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Teleop Cargo Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopCargoPoints}
          </TableCell>
        </TableRow>

        {/* Robot 1 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endgameRobot1}
              teamKey={match.alliances.red.team_keys[0]}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Robot 1 Endgame
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endgameRobot1}
              teamKey={match.alliances.blue.team_keys[0]}
            />
          </TableCell>
        </TableRow>

        {/* Robot 2 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endgameRobot2}
              teamKey={match.alliances.red.team_keys[1]}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Robot 2 Endgame
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endgameRobot2}
              teamKey={match.alliances.blue.team_keys[1]}
            />
          </TableCell>
        </TableRow>

        {/* Robot 3 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endgameRobot3}
              teamKey={match.alliances.red.team_keys[2]}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Robot 3 Endgame
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endgameRobot3}
              teamKey={match.alliances.blue.team_keys[2]}
            />
          </TableCell>
        </TableRow>

        {/* Endgame Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.endgamePoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Endgame Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.endgamePoints}
          </TableCell>
        </TableRow>

        {/* Total Teleop */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Total Teleop
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopPoints}
          </TableCell>
        </TableRow>

        {/* Quintet Achieved */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.quintetAchieved ?? false}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Quintet Achieved
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.quintetAchieved ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Cargo Bonus RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.cargoBonusRankingPoint ?? false}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Cargo Bonus RP
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.cargoBonusRankingPoint ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Hangar Bonus RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.hangarBonusRankingPoint ?? false}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Hangar Bonus RP
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.hangarBonusRankingPoint ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.red.foulCount}
              pointsPerFoul={4}
              techFoulsReceived={scoreBreakdown.red.techFoulCount}
              pointsPerTechFoul={8}
              techOrMajor="tech"
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Fouls
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.blue.foulCount}
              pointsPerFoul={4}
              techFoulsReceived={scoreBreakdown.blue.techFoulCount}
              pointsPerTechFoul={8}
              techOrMajor="tech"
            />
          </TableCell>
        </TableRow>

        {/* Adjustments */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.adjustPoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Adjustments
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.adjustPoints}
          </TableCell>
        </TableRow>

        {/* Total Score */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.totalPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Total Score
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.totalPoints}
          </TableCell>
        </TableRow>

        {/* RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            +{scoreBreakdown.red.rp} RP
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            RP
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            +{scoreBreakdown.blue.rp} RP
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
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
