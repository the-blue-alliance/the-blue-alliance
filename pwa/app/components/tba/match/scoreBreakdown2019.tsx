import { Match, MatchScoreBreakdown2019 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';
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
    <Table className="table-fixed overflow-hidden rounded-lg text-center">
      <colgroup>
        <col />
        <col className="w-[45%]" />
        <col />
      </colgroup>
      <TableBody>
        {/* Sandstorm / HAB Line */}
        <TableRow>
          <TableCell
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={
                scoreBreakdown.red.habLineRobot1 === 'CrossedHabLineInSandstorm'
              }
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.red.habLineRobot2 === 'CrossedHabLineInSandstorm'
              }
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.red.habLineRobot3 === 'CrossedHabLineInSandstorm'
              }
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.red.sandStormBonusPoints})
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Sandstorm Bonus
          </TableCell>
          <TableCell
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={
                scoreBreakdown.blue.habLineRobot1 ===
                'CrossedHabLineInSandstorm'
              }
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.blue.habLineRobot2 ===
                'CrossedHabLineInSandstorm'
              }
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.blue.habLineRobot3 ===
                'CrossedHabLineInSandstorm'
              }
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.blue.sandStormBonusPoints})
          </TableCell>
        </TableRow>

        {/* Hatch Panel Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.hatchPanelPoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Hatch Panel Points
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.hatchPanelPoints}
          </TableCell>
        </TableRow>

        {/* Cargo Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.cargoPoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Cargo Points
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.cargoPoints}
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

        {/* HAB Climb Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.habClimbPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            HAB Climb Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.habClimbPoints}
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

        {/* Complete Rocket RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.completeRocketRankingPoint}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Complete Rocket
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.completeRocketRankingPoint}
            />
          </TableCell>
        </TableRow>

        {/* HAB Docking RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.habDockingRankingPoint}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            HAB Docking
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.habDockingRankingPoint}
            />
          </TableCell>
        </TableRow>

        {/* Fouls / Tech Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.red.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2019]}
              techFoulsReceived={scoreBreakdown.red.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2019]}
              techOrMajor="tech"
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Fouls / Tech Fouls
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.blue.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2019]}
              techFoulsReceived={scoreBreakdown.blue.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2019]}
              techOrMajor="tech"
            />
          </TableCell>
        </TableRow>

        {/* Adjustments */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.adjustPoints ?? 0}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Adjustments
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.adjustPoints ?? 0}
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
