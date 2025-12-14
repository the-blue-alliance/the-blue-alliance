import { MatchScoreBreakdown2015 } from '~/api/tba/read';
import {
  ScoreBreakdownAllianceCell,
  ScoreBreakdownLabelCell,
  ScoreBreakdownRow,
  ScoreBreakdownTable,
} from '~/components/tba/match/scoreBreakdown';
import {
  AUTO_CONTAINER_SET_2015_POINTS,
  AUTO_ROBOT_SET_2015_POINTS,
  AUTO_STACKED_TOTE_SET_2015_POINTS,
  AUTO_TOTE_SET_2015_POINTS,
} from '~/lib/pointValues';

export function ScoreBreakdown2015({
  scoreBreakdown,
}: {
  scoreBreakdown: MatchScoreBreakdown2015;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Robot Set */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.robot_set ? AUTO_ROBOT_SET_2015_POINTS : 0
        }
        redValue={scoreBreakdown.red.robot_set ? AUTO_ROBOT_SET_2015_POINTS : 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.robot_set ? AUTO_ROBOT_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.robot_set ? AUTO_ROBOT_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Container Set */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.container_set ? AUTO_CONTAINER_SET_2015_POINTS : 0
        }
        redValue={
          scoreBreakdown.red.container_set ? AUTO_CONTAINER_SET_2015_POINTS : 0
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.container_set
            ? AUTO_CONTAINER_SET_2015_POINTS
            : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Container Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.container_set
            ? AUTO_CONTAINER_SET_2015_POINTS
            : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Tote Set */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.tote_set ? AUTO_TOTE_SET_2015_POINTS : 0}
        redValue={scoreBreakdown.red.tote_set ? AUTO_TOTE_SET_2015_POINTS : 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.tote_set ? AUTO_TOTE_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Tote Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.tote_set ? AUTO_TOTE_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Stacked Tote Set */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.tote_stack ? AUTO_STACKED_TOTE_SET_2015_POINTS : 0
        }
        redValue={
          scoreBreakdown.red.tote_stack ? AUTO_STACKED_TOTE_SET_2015_POINTS : 0
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.tote_stack
            ? AUTO_STACKED_TOTE_SET_2015_POINTS
            : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Stacked Tote Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.tote_stack
            ? AUTO_STACKED_TOTE_SET_2015_POINTS
            : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Auto */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.auto_points ?? 0}
        redValue={scoreBreakdown.red.auto_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.auto_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Auto
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.auto_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Tote Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.tote_points ?? 0}
        redValue={scoreBreakdown.red.tote_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.tote_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Tote Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.tote_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Container Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.container_points ?? 0}
        redValue={scoreBreakdown.red.container_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.container_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Container Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.container_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Litter Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.litter_points ?? 0}
        redValue={scoreBreakdown.red.litter_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.litter_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Litter Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.litter_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Teleop */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.teleop_points ?? 0}
        redValue={scoreBreakdown.red.teleop_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleop_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Teleop
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleop_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Foul Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.foul_points ?? 0}
        redValue={scoreBreakdown.red.foul_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.foul_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Foul Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.foul_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Score */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.total_points ?? 0}
        redValue={scoreBreakdown.red.total_points ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.total_points}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Score
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.total_points}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
  );
}
