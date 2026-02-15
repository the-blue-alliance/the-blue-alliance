import { Match, MatchScoreBreakdown2017 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';
import { POINTS_PER_FOUL, POINTS_PER_TECH_FOUL } from '~/lib/pointValues';

export default function ScoreBreakdown2017({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2017;
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
        {/* Auto Mobility */}
        <TableRow>
          <TableCell
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.red.robot1Auto === 'Mobility'}
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.robot2Auto === 'Mobility'}
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.robot3Auto === 'Mobility'}
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.red.autoMobilityPoints})
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Auto Mobility
          </TableCell>
          <TableCell
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.robot1Auto === 'Mobility'}
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.robot2Auto === 'Mobility'}
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.robot3Auto === 'Mobility'}
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.blue.autoMobilityPoints})
          </TableCell>
        </TableRow>

        {/* Auto Fuel High */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoFuelHigh}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Fuel High
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoFuelHigh}
          </TableCell>
        </TableRow>

        {/* Auto Fuel Low */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoFuelLow}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Fuel Low
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoFuelLow}
          </TableCell>
        </TableRow>

        {/* Auto Fuel Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoFuelPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Auto Fuel Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoFuelPoints}
          </TableCell>
        </TableRow>

        {/* Auto Rotors */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <RotorDisplay
              rotor1={scoreBreakdown.red.rotor1Auto}
              rotor2={scoreBreakdown.red.rotor2Auto}
            />
            (+{scoreBreakdown.red.autoRotorPoints})
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Auto Rotors
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <RotorDisplay
              rotor1={scoreBreakdown.blue.rotor1Auto}
              rotor2={scoreBreakdown.blue.rotor2Auto}
            />
            (+{scoreBreakdown.blue.autoRotorPoints})
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

        {/* Teleop Fuel High */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopFuelHigh}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Fuel High
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopFuelHigh}
          </TableCell>
        </TableRow>

        {/* Teleop Fuel Low */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopFuelLow}
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Fuel Low
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopFuelLow}
          </TableCell>
        </TableRow>

        {/* Teleop Fuel Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopFuelPoints}
          </TableCell>
          <TableCell className="bg-neutral-200 dark:bg-neutral-800">
            Teleop Fuel Points
          </TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopFuelPoints}
          </TableCell>
        </TableRow>

        {/* Teleop Rotors */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <RotorDisplay
              rotor1={scoreBreakdown.red.rotor1Engaged}
              rotor2={scoreBreakdown.red.rotor2Engaged}
              rotor3={scoreBreakdown.red.rotor3Engaged}
              rotor4={scoreBreakdown.red.rotor4Engaged}
            />
            (+{scoreBreakdown.red.teleopRotorPoints})
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Teleop Rotors
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <RotorDisplay
              rotor1={scoreBreakdown.blue.rotor1Engaged}
              rotor2={scoreBreakdown.blue.rotor2Engaged}
              rotor3={scoreBreakdown.blue.rotor3Engaged}
              rotor4={scoreBreakdown.blue.rotor4Engaged}
            />
            (+{scoreBreakdown.blue.teleopRotorPoints})
          </TableCell>
        </TableRow>

        {/* Takeoff Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <TouchpadDisplay
              near={scoreBreakdown.red.touchpadNear}
              middle={scoreBreakdown.red.touchpadMiddle}
              far={scoreBreakdown.red.touchpadFar}
              teamKeys={match.alliances.red.team_keys}
            />
            (+{scoreBreakdown.red.teleopTakeoffPoints})
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Takeoff
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <TouchpadDisplay
              near={scoreBreakdown.blue.touchpadNear}
              middle={scoreBreakdown.blue.touchpadMiddle}
              far={scoreBreakdown.blue.touchpadFar}
              teamKeys={match.alliances.blue.team_keys}
            />
            (+{scoreBreakdown.blue.teleopTakeoffPoints})
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

        {/* kPa Bonus RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.kPaRankingPointAchieved}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Pressure Reached
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.kPaRankingPointAchieved}
            />
          </TableCell>
        </TableRow>

        {/* Rotor Bonus RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.rotorRankingPointAchieved}
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            All Rotors Engaged
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.rotorRankingPointAchieved}
            />
          </TableCell>
        </TableRow>

        {/* Fouls / Tech Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.red.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2017]}
              techFoulsReceived={scoreBreakdown.red.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2017]}
              techOrMajor="tech"
            />
          </TableCell>
          <TableCell className="bg-neutral-50 dark:bg-neutral-950">
            Fouls / Tech Fouls
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.blue.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2017]}
              techFoulsReceived={scoreBreakdown.blue.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2017]}
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
