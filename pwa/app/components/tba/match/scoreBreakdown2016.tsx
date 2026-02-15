import { Match, MatchScoreBreakdown2016 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';
import { POINTS_PER_FOUL, POINTS_PER_TECH_FOUL } from '~/lib/pointValues';

export default function ScoreBreakdown2016({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2016;
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
        {/* Auto Reach/Cross */}
        <TableRow>
          <TableCell
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={
                scoreBreakdown.red.robot1Auto === 'Crossed' ||
                scoreBreakdown.red.robot1Auto === 'Reached'
              }
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.red.robot2Auto === 'Crossed' ||
                scoreBreakdown.red.robot2Auto === 'Reached'
              }
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.red.robot3Auto === 'Crossed' ||
                scoreBreakdown.red.robot3Auto === 'Reached'
              }
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Auto Reach/Cross
          </TableCell>
          <TableCell
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={
                scoreBreakdown.blue.robot1Auto === 'Crossed' ||
                scoreBreakdown.blue.robot1Auto === 'Reached'
              }
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.blue.robot2Auto === 'Crossed' ||
                scoreBreakdown.blue.robot2Auto === 'Reached'
              }
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={
                scoreBreakdown.blue.robot3Auto === 'Crossed' ||
                scoreBreakdown.blue.robot3Auto === 'Reached'
              }
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
          </TableCell>
        </TableRow>

        {/* Auto Reach Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoReachPoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Reach Points
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoReachPoints}
          </TableCell>
        </TableRow>

        {/* Auto Crossing Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoCrossingPoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Crossing Points
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoCrossingPoints}
          </TableCell>
        </TableRow>

        {/* Auto Boulders */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            H: {scoreBreakdown.red.autoBouldersHigh ?? 0} / L:{' '}
            {scoreBreakdown.red.autoBouldersLow ?? 0} (+
            {scoreBreakdown.red.autoBoulderPoints})
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Boulders
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            H: {scoreBreakdown.blue.autoBouldersHigh ?? 0} / L:{' '}
            {scoreBreakdown.blue.autoBouldersLow ?? 0} (+
            {scoreBreakdown.blue.autoBoulderPoints})
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

        {/* Teleop Crossing Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopCrossingPoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Crossing Points
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopCrossingPoints}
          </TableCell>
        </TableRow>

        {/* Teleop Boulders */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            H: {scoreBreakdown.red.teleopBouldersHigh} / L:{' '}
            {scoreBreakdown.red.teleopBouldersLow} (+
            {scoreBreakdown.red.teleopBoulderPoints})
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Boulders
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            H: {scoreBreakdown.blue.teleopBouldersHigh} / L:{' '}
            {scoreBreakdown.blue.teleopBouldersLow} (+
            {scoreBreakdown.blue.teleopBoulderPoints})
          </TableCell>
        </TableRow>

        {/* Challenge/Scale Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopChallengePoints +
              scoreBreakdown.red.teleopScalePoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Tower Challenge/Scale
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopChallengePoints +
              scoreBreakdown.blue.teleopScalePoints}
          </TableCell>
        </TableRow>

        {/* Total Teleop */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopPoints ?? 0}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Total Teleop
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopPoints ?? 0}
          </TableCell>
        </TableRow>

        {/* Breached RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.teleopDefensesBreached}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Defenses Breached
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.teleopDefensesBreached}
            />
          </TableCell>
        </TableRow>

        {/* Tower Captured RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.teleopTowerCaptured}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Tower Captured
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.teleopTowerCaptured}
            />
          </TableCell>
        </TableRow>

        {/* Breach / Capture Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.breachPoints} /{' '}
            {scoreBreakdown.red.capturePoints}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Breach / Capture Points
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.breachPoints} /{' '}
            {scoreBreakdown.blue.capturePoints}
          </TableCell>
        </TableRow>

        {/* Fouls / Tech Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.red.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2016]}
              techFoulsReceived={scoreBreakdown.red.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2016]}
              techOrMajor="tech"
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Fouls / Tech Fouls
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.blue.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2016]}
              techFoulsReceived={scoreBreakdown.blue.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2016]}
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
            +{scoreBreakdown.red.tba_rpEarned ?? 0} RP
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            RP
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            +{scoreBreakdown.blue.tba_rpEarned ?? 0} RP
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}
