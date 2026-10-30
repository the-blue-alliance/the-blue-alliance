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

export default function ScoreBreakdown2015({
  scoreBreakdown,
}: {
  scoreBreakdown: MatchScoreBreakdown2015;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Robot Set */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.robotSet ? AUTO_ROBOT_SET_2015_POINTS : 0
        }
        redValue={scoreBreakdown.red.robotSet ? AUTO_ROBOT_SET_2015_POINTS : 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.robotSet ? AUTO_ROBOT_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Robot Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.robotSet ? AUTO_ROBOT_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Container Set */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.containerSet ? AUTO_CONTAINER_SET_2015_POINTS : 0
        }
        redValue={
          scoreBreakdown.red.containerSet ? AUTO_CONTAINER_SET_2015_POINTS : 0
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.containerSet ? AUTO_CONTAINER_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Container Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.containerSet
            ? AUTO_CONTAINER_SET_2015_POINTS
            : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Tote Set */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.toteSet ? AUTO_TOTE_SET_2015_POINTS : 0}
        redValue={scoreBreakdown.red.toteSet ? AUTO_TOTE_SET_2015_POINTS : 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.toteSet ? AUTO_TOTE_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Tote Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.toteSet ? AUTO_TOTE_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Stacked Tote Set */}
      <ScoreBreakdownRow
        blueValue={
          scoreBreakdown.blue.toteStack ? AUTO_STACKED_TOTE_SET_2015_POINTS : 0
        }
        redValue={
          scoreBreakdown.red.toteStack ? AUTO_STACKED_TOTE_SET_2015_POINTS : 0
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.toteStack ? AUTO_STACKED_TOTE_SET_2015_POINTS : 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Stacked Tote Set
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.toteStack
            ? AUTO_STACKED_TOTE_SET_2015_POINTS
            : 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Auto */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.autoPoints ?? 0}
        redValue={scoreBreakdown.red.autoPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.autoPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Auto
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.autoPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Tote Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.totePoints ?? 0}
        redValue={scoreBreakdown.red.totePoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.totePoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Tote Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.totePoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Container Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.containerPoints ?? 0}
        redValue={scoreBreakdown.red.containerPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.containerPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Container Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.containerPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Litter Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.litterPoints ?? 0}
        redValue={scoreBreakdown.red.litterPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.litterPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Litter Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.litterPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Teleop */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.teleopPoints ?? 0}
        redValue={scoreBreakdown.red.teleopPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Teleop
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Foul Points */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.foulPoints ?? 0}
        redValue={scoreBreakdown.red.foulPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.foulPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Foul Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.foulPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Score */}
      <ScoreBreakdownRow
        blueValue={scoreBreakdown.blue.totalPoints ?? 0}
        redValue={scoreBreakdown.red.totalPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.totalPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Total Score
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.totalPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
  );
}
