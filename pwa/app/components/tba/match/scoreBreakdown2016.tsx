import { Match, MatchScoreBreakdown2016 } from '~/api/tba/read';
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
import { POINTS_PER_FOUL, POINTS_PER_TECH_FOUL } from '~/lib/pointValues';

export default function ScoreBreakdown2016({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2016;
  match: Match;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Auto Reach/Cross */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell
          color="red"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={
              scoreBreakdown.red.robot1Auto === 'Crossed' ||
              scoreBreakdown.red.robot1Auto === 'Reached'
            }
            teamKey={match.alliances.red.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.red.robot2Auto === 'Crossed' ||
              scoreBreakdown.red.robot2Auto === 'Reached'
            }
            teamKey={match.alliances.red.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.red.robot3Auto === 'Crossed' ||
              scoreBreakdown.red.robot3Auto === 'Reached'
            }
            teamKey={match.alliances.red.team_keys[2]}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Auto Reach/Cross
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={
              scoreBreakdown.blue.robot1Auto === 'Crossed' ||
              scoreBreakdown.blue.robot1Auto === 'Reached'
            }
            teamKey={match.alliances.blue.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.blue.robot2Auto === 'Crossed' ||
              scoreBreakdown.blue.robot2Auto === 'Reached'
            }
            teamKey={match.alliances.blue.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={
              scoreBreakdown.blue.robot3Auto === 'Crossed' ||
              scoreBreakdown.blue.robot3Auto === 'Reached'
            }
            teamKey={match.alliances.blue.team_keys[2]}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Reach Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoReachPoints}
        blueValue={scoreBreakdown.blue.autoReachPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoReachPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Reach Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoReachPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Crossing Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoCrossingPoints}
        blueValue={scoreBreakdown.blue.autoCrossingPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoCrossingPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Crossing Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoCrossingPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Boulders */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoBoulderPoints}
        blueValue={scoreBreakdown.blue.autoBoulderPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          H: {scoreBreakdown.red.autoBouldersHigh ?? 0} / L:{' '}
          {scoreBreakdown.red.autoBouldersLow ?? 0} (+
          {scoreBreakdown.red.autoBoulderPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Boulders
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          H: {scoreBreakdown.blue.autoBouldersHigh ?? 0} / L:{' '}
          {scoreBreakdown.blue.autoBouldersLow ?? 0} (+
          {scoreBreakdown.blue.autoBoulderPoints})
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

      {/* Teleop Crossing Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopCrossingPoints}
        blueValue={scoreBreakdown.blue.teleopCrossingPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopCrossingPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Crossing Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopCrossingPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Boulders */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopBoulderPoints}
        blueValue={scoreBreakdown.blue.teleopBoulderPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          H: {scoreBreakdown.red.teleopBouldersHigh} / L:{' '}
          {scoreBreakdown.red.teleopBouldersLow} (+
          {scoreBreakdown.red.teleopBoulderPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Boulders
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          H: {scoreBreakdown.blue.teleopBouldersHigh} / L:{' '}
          {scoreBreakdown.blue.teleopBouldersLow} (+
          {scoreBreakdown.blue.teleopBoulderPoints})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Challenge/Scale Points */}
      <ScoreBreakdownRow
        redValue={
          scoreBreakdown.red.teleopChallengePoints +
          scoreBreakdown.red.teleopScalePoints
        }
        blueValue={
          scoreBreakdown.blue.teleopChallengePoints +
          scoreBreakdown.blue.teleopScalePoints
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopChallengePoints +
            scoreBreakdown.red.teleopScalePoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Tower Challenge/Scale
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopChallengePoints +
            scoreBreakdown.blue.teleopScalePoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Total Teleop */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopPoints ?? 0}
        blueValue={scoreBreakdown.blue.teleopPoints ?? 0}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopPoints ?? 0}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark" fontWeight="bold">
          Total Teleop
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopPoints ?? 0}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Breached RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.teleopDefensesBreached}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Defenses Breached
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.teleopDefensesBreached}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Tower Captured RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.teleopTowerCaptured}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Tower Captured
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.teleopTowerCaptured}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Breach / Capture Points */}
      <ScoreBreakdownRow
        redValue={
          scoreBreakdown.red.breachPoints + scoreBreakdown.red.capturePoints
        }
        blueValue={
          scoreBreakdown.blue.breachPoints + scoreBreakdown.blue.capturePoints
        }
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.breachPoints} /{' '}
          {scoreBreakdown.red.capturePoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Breach / Capture Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.breachPoints} /{' '}
          {scoreBreakdown.blue.capturePoints}
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
            pointsPerFoul={POINTS_PER_FOUL[2016]}
            techFoulsReceived={scoreBreakdown.red.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2016]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Fouls / Tech Fouls
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.blue.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2016]}
            techFoulsReceived={scoreBreakdown.blue.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2016]}
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
          +{scoreBreakdown.red.tba_rpEarned ?? 0} RP
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">RP</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          +{scoreBreakdown.blue.tba_rpEarned ?? 0} RP
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>
    </ScoreBreakdownTable>
  );
}
