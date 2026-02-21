import { Match, MatchScoreBreakdown2017 } from '~/api/tba/read';
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

export default function ScoreBreakdown2017({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2017;
  match: Match;
}) {
  return (
    <ScoreBreakdownTable>
      {/* Auto Mobility */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoMobilityPoints}
        blueValue={scoreBreakdown.blue.autoMobilityPoints}
      >
        <ScoreBreakdownAllianceCell
          color="red"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={scoreBreakdown.red.robot1Auto === 'Mobility'}
            teamKey={match.alliances.red.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.red.robot2Auto === 'Mobility'}
            teamKey={match.alliances.red.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.red.robot3Auto === 'Mobility'}
            teamKey={match.alliances.red.team_keys[2]}
          />
          (+{scoreBreakdown.red.autoMobilityPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Auto Mobility
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell
          color="blue"
          shade="dark"
          className="whitespace-nowrap *:align-middle"
        >
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.robot1Auto === 'Mobility'}
            teamKey={match.alliances.blue.team_keys[0]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.robot2Auto === 'Mobility'}
            teamKey={match.alliances.blue.team_keys[1]}
          />
          <ConditionalCheckmark
            condition={scoreBreakdown.blue.robot3Auto === 'Mobility'}
            teamKey={match.alliances.blue.team_keys[2]}
          />
          (+{scoreBreakdown.blue.autoMobilityPoints})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Fuel High */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoFuelHigh}
        blueValue={scoreBreakdown.blue.autoFuelHigh}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoFuelHigh}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Fuel High
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoFuelHigh}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Fuel Low */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoFuelLow}
        blueValue={scoreBreakdown.blue.autoFuelLow}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.autoFuelLow}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Fuel Low
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.autoFuelLow}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Fuel Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoFuelPoints}
        blueValue={scoreBreakdown.blue.autoFuelPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.autoFuelPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Auto Fuel Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.autoFuelPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Auto Rotors */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.autoRotorPoints}
        blueValue={scoreBreakdown.blue.autoRotorPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <RotorDisplay
            rotor1={scoreBreakdown.red.rotor1Auto}
            rotor2={scoreBreakdown.red.rotor2Auto}
          />
          (+{scoreBreakdown.red.autoRotorPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Auto Rotors
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <RotorDisplay
            rotor1={scoreBreakdown.blue.rotor1Auto}
            rotor2={scoreBreakdown.blue.rotor2Auto}
          />
          (+{scoreBreakdown.blue.autoRotorPoints})
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

      {/* Teleop Fuel High */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopFuelHigh}
        blueValue={scoreBreakdown.blue.teleopFuelHigh}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopFuelHigh}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Fuel High
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopFuelHigh}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Fuel Low */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopFuelLow}
        blueValue={scoreBreakdown.blue.teleopFuelLow}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          {scoreBreakdown.red.teleopFuelLow}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Fuel Low
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          {scoreBreakdown.blue.teleopFuelLow}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Fuel Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopFuelPoints}
        blueValue={scoreBreakdown.blue.teleopFuelPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="dark">
          {scoreBreakdown.red.teleopFuelPoints}
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="dark">
          Teleop Fuel Points
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="dark">
          {scoreBreakdown.blue.teleopFuelPoints}
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Teleop Rotors */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopRotorPoints}
        blueValue={scoreBreakdown.blue.teleopRotorPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <RotorDisplay
            rotor1={scoreBreakdown.red.rotor1Engaged}
            rotor2={scoreBreakdown.red.rotor2Engaged}
            rotor3={scoreBreakdown.red.rotor3Engaged}
            rotor4={scoreBreakdown.red.rotor4Engaged}
          />
          (+{scoreBreakdown.red.teleopRotorPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Teleop Rotors
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <RotorDisplay
            rotor1={scoreBreakdown.blue.rotor1Engaged}
            rotor2={scoreBreakdown.blue.rotor2Engaged}
            rotor3={scoreBreakdown.blue.rotor3Engaged}
            rotor4={scoreBreakdown.blue.rotor4Engaged}
          />
          (+{scoreBreakdown.blue.teleopRotorPoints})
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Takeoff Points */}
      <ScoreBreakdownRow
        redValue={scoreBreakdown.red.teleopTakeoffPoints}
        blueValue={scoreBreakdown.blue.teleopTakeoffPoints}
      >
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <TouchpadDisplay
            near={scoreBreakdown.red.touchpadNear}
            middle={scoreBreakdown.red.touchpadMiddle}
            far={scoreBreakdown.red.touchpadFar}
            teamKeys={match.alliances.red.team_keys}
          />
          (+{scoreBreakdown.red.teleopTakeoffPoints})
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">Takeoff</ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <TouchpadDisplay
            near={scoreBreakdown.blue.touchpadNear}
            middle={scoreBreakdown.blue.touchpadMiddle}
            far={scoreBreakdown.blue.touchpadFar}
            teamKeys={match.alliances.blue.team_keys}
          />
          (+{scoreBreakdown.blue.teleopTakeoffPoints})
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

      {/* kPa Bonus RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.kPaRankingPointAchieved}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Pressure Reached
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.kPaRankingPointAchieved}
          />
        </ScoreBreakdownAllianceCell>
      </ScoreBreakdownRow>

      {/* Rotor Bonus RP */}
      <ScoreBreakdownRow>
        <ScoreBreakdownAllianceCell color="red" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.red.rotorRankingPointAchieved}
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          All Rotors Engaged
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <ConditionalRpAchieved
            condition={scoreBreakdown.blue.rotorRankingPointAchieved}
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
            foulsReceived={scoreBreakdown.red.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2017]}
            techFoulsReceived={scoreBreakdown.red.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2017]}
            techOrMajor="tech"
          />
        </ScoreBreakdownAllianceCell>
        <ScoreBreakdownLabelCell shade="light">
          Fouls / Tech Fouls
        </ScoreBreakdownLabelCell>
        <ScoreBreakdownAllianceCell color="blue" shade="light">
          <FoulDisplay
            foulsReceived={scoreBreakdown.blue.foulCount}
            pointsPerFoul={POINTS_PER_FOUL[2017]}
            techFoulsReceived={scoreBreakdown.blue.techFoulCount}
            pointsPerTechFoul={POINTS_PER_TECH_FOUL[2017]}
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

function RotorDisplay({
  rotor1,
  rotor2,
  rotor3,
  rotor4,
}: {
  rotor1: boolean;
  rotor2: boolean;
  rotor3?: boolean;
  rotor4?: boolean;
}) {
  return (
    <div className="flex items-center justify-center gap-1">
      <Badge variant={rotor1 ? 'secondary' : 'outline'}>R1</Badge>
      <Badge variant={rotor2 ? 'secondary' : 'outline'}>R2</Badge>
      {rotor3 !== undefined && (
        <Badge variant={rotor3 ? 'secondary' : 'outline'}>R3</Badge>
      )}
      {rotor4 !== undefined && (
        <Badge variant={rotor4 ? 'secondary' : 'outline'}>R4</Badge>
      )}
    </div>
  );
}

function TouchpadDisplay({
  near,
  middle,
  far,
  teamKeys,
}: {
  near?: string;
  middle?: string;
  far?: string;
  teamKeys: string[];
}) {
  return (
    <div className="flex items-center justify-center gap-1">
      <Badge
        variant={near === 'ReadyForTakeoff' ? 'secondary' : 'outline'}
        title={teamKeys[0]?.substring(3)}
      >
        {teamKeys[0]?.substring(3)}
      </Badge>
      <Badge
        variant={middle === 'ReadyForTakeoff' ? 'secondary' : 'outline'}
        title={teamKeys[1]?.substring(3)}
      >
        {teamKeys[1]?.substring(3)}
      </Badge>
      <Badge
        variant={far === 'ReadyForTakeoff' ? 'secondary' : 'outline'}
        title={teamKeys[2]?.substring(3)}
      >
        {teamKeys[2]?.substring(3)}
      </Badge>
    </div>
  );
}
