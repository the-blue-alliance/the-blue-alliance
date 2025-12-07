import { Match, MatchScoreBreakdown2025 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';

export default function ScoreBreakdown2025({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2025;
  match: Match;
}) {
  return (
    <Table className="table-fixed text-center">
      <colgroup>
        <col />
        <col />
        <col className="w-[45%]" />
        <col />
        <col />
      </colgroup>
      <TableBody>
        {/* Auto Leave */}
        <TableRow>
          <TableCell
            colSpan={2}
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.red.autoLineRobot1 === 'Yes'}
              teamKey={match.alliances.red.team_keys[0]}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.autoLineRobot2 === 'Yes'}
              teamKey={match.alliances.red.team_keys[1]}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.autoLineRobot3 === 'Yes'}
              teamKey={match.alliances.red.team_keys[2]}
            />
            (+{scoreBreakdown.red.autoMobilityPoints})
          </TableCell>
          <TableCell className="bg-gray-200">Auto Leave</TableCell>
          <TableCell
            colSpan={2}
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.autoLineRobot1 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[0]}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.autoLineRobot2 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[1]}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.autoLineRobot3 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[2]}
            />
            (+{scoreBreakdown.blue.autoMobilityPoints})
          </TableCell>
        </TableRow>

        {/* Auto Coral Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">L4</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoReef?.tba_topRowCount}
          </TableCell>
          <TableCell className="bg-gray-50" rowSpan={4}>
            Auto Coral Count
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoReef?.tba_topRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L4</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="bg-alliance-red-light">L3</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoReef?.tba_midRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoReef?.tba_midRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L3</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="bg-alliance-red-light">L2</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoReef?.tba_botRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoReef?.tba_botRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L2</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="bg-alliance-red-light">L1</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoReef?.trough}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoReef?.trough}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L1</TableCell>
        </TableRow>

        {/* Auto Coral Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.autoCoralPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Auto Coral Points</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.autoCoralPoints}
          </TableCell>
        </TableRow>

        {/* Total Auto */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.autoPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Total Auto</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.autoPoints}
          </TableCell>
        </TableRow>

        {/* Teleop Coral Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">L4</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopReef?.tba_topRowCount}
          </TableCell>
          <TableCell className="bg-gray-50" rowSpan={4}>
            Teleop Coral Count
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopReef?.tba_topRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L4</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="bg-alliance-red-light">L3</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopReef?.tba_midRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopReef?.tba_midRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L3</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="bg-alliance-red-light">L2</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopReef?.tba_botRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopReef?.tba_botRowCount}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L2</TableCell>
        </TableRow>
        <TableRow>
          <TableCell className="bg-alliance-red-light">L1</TableCell>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopReef?.trough}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopReef?.trough}
          </TableCell>
          <TableCell className="bg-alliance-blue-light">L1</TableCell>
        </TableRow>

        {/* Teleop Coral Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.teleopCoralPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Teleop Coral Points</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.teleopCoralPoints}
          </TableCell>
        </TableRow>

        {/* Processor Algae Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            {scoreBreakdown.red.wallAlgaeCount}
          </TableCell>
          <TableCell className="bg-gray-50">Processor Algae Count</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            {scoreBreakdown.blue.wallAlgaeCount}
          </TableCell>
        </TableRow>

        {/* Net Algae Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            {scoreBreakdown.red.netAlgaeCount}
          </TableCell>
          <TableCell className="bg-gray-50">Net Algae Count</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            {scoreBreakdown.blue.netAlgaeCount}
          </TableCell>
        </TableRow>

        {/* Algae Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.algaePoints}
          </TableCell>
          <TableCell className="bg-gray-200">Algae Points</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.algaePoints}
          </TableCell>
        </TableRow>

        {/* Robot 1 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameRobot1}
              teamKey={match.alliances.red.team_keys[0]}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 1 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameRobot1}
              teamKey={match.alliances.blue.team_keys[0]}
            />
          </TableCell>
        </TableRow>

        {/* Robot 2 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameRobot2}
              teamKey={match.alliances.red.team_keys[1]}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 2 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameRobot2}
              teamKey={match.alliances.blue.team_keys[1]}
            />
          </TableCell>
        </TableRow>

        {/* Robot 3 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameRobot3}
              teamKey={match.alliances.red.team_keys[2]}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 3 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameRobot3}
              teamKey={match.alliances.blue.team_keys[2]}
            />
          </TableCell>
        </TableRow>

        {/* Barge Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.endGameBargePoints}
          </TableCell>
          <TableCell className="bg-gray-200">Barge Points</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.endGameBargePoints}
          </TableCell>
        </TableRow>

        {/* Total Teleop */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.teleopPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Total Teleop</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.teleopPoints}
          </TableCell>
        </TableRow>

        {/* Coopertition Criteria Met */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.coopertitionCriteriaMet ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">
            Coopertition Criteria Met
          </TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.coopertitionCriteriaMet ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Auto Bonus */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.autoBonusAchieved ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Auto Bonus</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.autoBonusAchieved ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Coral Bonus */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.coralBonusAchieved ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Coral Bonus</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.coralBonusAchieved ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Barge Bonus */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.bargeBonusAchieved ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Barge Bonus</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.bargeBonusAchieved ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Fouls / Major Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            {scoreBreakdown.red.foulCount} / {scoreBreakdown.red.techFoulCount}
          </TableCell>
          <TableCell className="bg-gray-50">Fouls / Major Fouls</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            {scoreBreakdown.blue.foulCount} /{' '}
            {scoreBreakdown.blue.techFoulCount}
          </TableCell>
        </TableRow>

        {/* Foul Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.foulPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Foul Points</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.foulPoints}
          </TableCell>
        </TableRow>

        {/* Adjustments */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            {scoreBreakdown.red.adjustPoints}
          </TableCell>
          <TableCell className="bg-gray-50">Adjustments</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
            {scoreBreakdown.blue.adjustPoints}
          </TableCell>
        </TableRow>

        {/* Total Score */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark" colSpan={2}>
            {scoreBreakdown.red.totalPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Total Score</TableCell>
          <TableCell className="bg-alliance-blue-dark" colSpan={2}>
            {scoreBreakdown.blue.totalPoints}
          </TableCell>
        </TableRow>

        {/* RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light" colSpan={2}>
            +{scoreBreakdown.red.rp} RP
          </TableCell>
          <TableCell className="bg-gray-50">RP</TableCell>
          <TableCell className="bg-alliance-blue-light" colSpan={2}>
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
  endgame: MatchScoreBreakdown2025['red']['endGameRobot1'];
  teamKey: string;
}) {
  const pointMap: Record<
    NonNullable<MatchScoreBreakdown2025['red']['endGameRobot1']>,
    number
  > = {
    DeepCage: 12,
    ShallowCage: 6,
    Parked: 2,
    None: 0,
  };

  const displayMap: Record<
    NonNullable<MatchScoreBreakdown2025['red']['endGameRobot1']>,
    string
  > = {
    DeepCage: 'Deep Cage',
    ShallowCage: 'Shallow Cage',
    Parked: 'Parked',
    None: 'None',
  };

  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant={'outline'}>{teamKey.substring(3)}</Badge>
      {displayMap[endgame ?? 'None']} (+{pointMap[endgame ?? 'None']})
    </div>
  );
}
