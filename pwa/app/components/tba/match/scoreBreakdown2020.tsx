import { Match, MatchScoreBreakdown2020 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';
import { POINTS_PER_FOUL, POINTS_PER_TECH_FOUL } from '~/lib/pointValues';

const ENDGAME_2020_POINTS: Record<string, number> = {
  Hang: 25,
  Park: 5,
  None: 0,
};

export default function ScoreBreakdown2020({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2020;
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
        {/* Initiation Line */}
        <TableRow>
          <TableCell
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.red.initLineRobot1 === 'Exited'}
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.initLineRobot2 === 'Exited'}
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.initLineRobot3 === 'Exited'}
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.red.autoInitLinePoints})
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Initiation Line
          </TableCell>
          <TableCell
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.initLineRobot1 === 'Exited'}
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.initLineRobot2 === 'Exited'}
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.initLineRobot3 === 'Exited'}
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.blue.autoInitLinePoints})
          </TableCell>
        </TableRow>

        {/* Auto Power Cells Bottom */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoCellsBottom}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Bottom Port
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoCellsBottom}
          </TableCell>
        </TableRow>

        {/* Auto Power Cells Outer */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoCellsOuter}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Outer Port
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoCellsOuter}
          </TableCell>
        </TableRow>

        {/* Auto Power Cells Inner */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoCellsInner}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Inner Port
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoCellsInner}
          </TableCell>
        </TableRow>

        {/* Auto Cell Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoCellPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Auto Cell Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoCellPoints}
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

        {/* Teleop Power Cells Bottom */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopCellsBottom}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Bottom Port
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopCellsBottom}
          </TableCell>
        </TableRow>

        {/* Teleop Power Cells Outer */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopCellsOuter}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Outer Port
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopCellsOuter}
          </TableCell>
        </TableRow>

        {/* Teleop Power Cells Inner */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopCellsInner}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Inner Port
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopCellsInner}
          </TableCell>
        </TableRow>

        {/* Teleop Cell Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopCellPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Teleop Cell Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopCellPoints}
          </TableCell>
        </TableRow>

        {/* Control Panel */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ControlPanelCell
              stage1Activated={scoreBreakdown.red.stage1Activated}
              stage2Activated={scoreBreakdown.red.stage2Activated}
              stage3Activated={scoreBreakdown.red.stage3Activated}
              controlPanelPoints={scoreBreakdown.red.controlPanelPoints}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Control Panel
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ControlPanelCell
              stage1Activated={scoreBreakdown.blue.stage1Activated}
              stage2Activated={scoreBreakdown.blue.stage2Activated}
              stage3Activated={scoreBreakdown.blue.stage3Activated}
              controlPanelPoints={scoreBreakdown.blue.controlPanelPoints}
            />
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

        {/* Rung Level */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.endgameRungIsLevel === 'IsLevel'}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Rung Level
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.endgameRungIsLevel === 'IsLevel'}
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

        {/* Shield Operational RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.shieldOperationalRankingPoint}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Shield Operational
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.shieldOperationalRankingPoint}
            />
          </TableCell>
        </TableRow>

        {/* Shield Energized RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.shieldEnergizedRankingPoint}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Shield Energized
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.shieldEnergizedRankingPoint}
            />
          </TableCell>
        </TableRow>

        {/* Fouls / Tech Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.red.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2020]}
              techFoulsReceived={scoreBreakdown.red.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2020]}
              techOrMajor="tech"
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Fouls / Tech Fouls
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.blue.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2020]}
              techFoulsReceived={scoreBreakdown.blue.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2020]}
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
            +{scoreBreakdown.red.rp ?? 0} RP
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            RP
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            +{scoreBreakdown.blue.rp ?? 0} RP
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}

interface ControlPanelCellProps {
  stage1Activated: boolean;
  stage2Activated: boolean;
  stage3Activated: boolean;
  controlPanelPoints: number;
}

function ControlPanelCell({
  stage1Activated,
  stage2Activated,
  stage3Activated,
  controlPanelPoints,
}: ControlPanelCellProps) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="flex items-center gap-2">
        <Badge variant={stage1Activated ? 'secondary' : 'outline'}>S1</Badge>
        <Badge variant={stage2Activated ? 'secondary' : 'outline'}>S2</Badge>
        <Badge variant={stage3Activated ? 'secondary' : 'outline'}>S3</Badge>
      </div>
      <span>(+{controlPanelPoints})</span>
    </div>
  );
}

interface EndgameRobotCellProps {
  endgame: MatchScoreBreakdown2020['red']['endgameRobot1'];
  teamKey: string;
}

function EndgameRobotCell({ endgame, teamKey }: EndgameRobotCellProps) {
  const points = ENDGAME_2020_POINTS[endgame] ?? 0;

  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant={'outline'}>{teamKey.substring(3)}</Badge>
      {endgame} (+{points})
    </div>
  );
}
