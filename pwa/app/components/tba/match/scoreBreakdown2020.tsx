import { Match, MatchScoreBreakdown2020 } from '~/api/tba/read';
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
    <ScoreBreakdownTable>
      {/* Initiation Line */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoInitLinePoints}
        blueValue={scoreBreakdown.blue.autoInitLinePoints}
      >
        <ScoreBreakdownAllianceCell
          color="red"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={scoreBreakdown.red.initLineRobot1 === 'Exited'}
            teamKey={match.alliances.red.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.red.initLineRobot2 === 'Exited'}
            teamKey={match.alliances.red.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.red.initLineRobot3 === 'Exited'}
            teamKey={match.alliances.red.team_keys[2]}
          />
          (+{scoreBreakdown.red.autoInitLinePoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Initiation Line
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.initLineRobot1 === 'Exited'}
            teamKey={match.alliances.blue.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.initLineRobot2 === 'Exited'}
            teamKey={match.alliances.blue.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.initLineRobot3 === 'Exited'}
            teamKey={match.alliances.blue.team_keys[2]}
          />
          (+{scoreBreakdown.blue.autoInitLinePoints})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Power Cells Bottom */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCellsBottom}
        blueValue={scoreBreakdown.blue.autoCellsBottom}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoCellsBottom}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Bottom Port
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoCellsBottom}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Power Cells Outer */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCellsOuter}
        blueValue={scoreBreakdown.blue.autoCellsOuter}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoCellsOuter}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Outer Port
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoCellsOuter}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Power Cells Inner */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCellsInner}
        blueValue={scoreBreakdown.blue.autoCellsInner}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoCellsInner}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Inner Port
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoCellsInner}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Cell Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCellPoints}
        blueValue={scoreBreakdown.blue.autoCellPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.autoCellPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Auto Cell Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.autoCellPoints}
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

      {/* Teleop Power Cells Bottom */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCellsBottom}
        blueValue={scoreBreakdown.blue.teleopCellsBottom}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopCellsBottom}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Bottom Port
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopCellsBottom}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Power Cells Outer */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCellsOuter}
        blueValue={scoreBreakdown.blue.teleopCellsOuter}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopCellsOuter}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Outer Port
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopCellsOuter}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Power Cells Inner */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCellsInner}
        blueValue={scoreBreakdown.blue.teleopCellsInner}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopCellsInner}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Inner Port
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopCellsInner}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Cell Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCellPoints}
        blueValue={scoreBreakdown.blue.teleopCellPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopCellPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Teleop Cell Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopCellPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Control Panel */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.controlPanelPoints}
        blueValue={scoreBreakdown.blue.controlPanelPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ControlPanelCell
            stage1Activated={scoreBreakdown.red.stage1Activated}
            stage2Activated={scoreBreakdown.red.stage2Activated}
            stage3Activated={scoreBreakdown.red.stage3Activated}
            controlPanelPoints={scoreBreakdown.red.controlPanelPoints}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Control Panel
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ControlPanelCell
            stage1Activated={scoreBreakdown.blue.stage1Activated}
            stage2Activated={scoreBreakdown.blue.stage2Activated}
            stage3Activated={scoreBreakdown.blue.stage3Activated}
            controlPanelPoints={scoreBreakdown.blue.controlPanelPoints}
          />
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

      {/* Rung Level */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.endgameRungIsLevel === 'IsLevel'}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Rung Level
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.endgameRungIsLevel === 'IsLevel'}
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

      {/* Shield Operational RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.shieldOperationalRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Shield Operational
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.shieldOperationalRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Shield Energized RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.shieldEnergizedRankingPoint}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Shield Energized
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.shieldEnergizedRankingPoint}
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
            foulsReceived={scoreBreakdown.blue.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2020]}
            techFoulsReceived={scoreBreakdown.blue.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2020]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Fouls / Tech Fouls
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.red.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2020]}
            techFoulsReceived={scoreBreakdown.red.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2020]}
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
          +{scoreBreakdown.red.rp ?? 0} RP
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">RP</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          +{scoreBreakdown.blue.rp ?? 0} RP
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
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
