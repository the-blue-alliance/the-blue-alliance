import { Match, MatchScoreBreakdown2023 } from '~/api/tba/read';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
  FoulDisplay,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';
import { POINTS_PER_FOUL, POINTS_PER_TECH_FOUL } from '~/lib/pointValues';

export default function ScoreBreakdown2023({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2023;
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
        {/* Mobility */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            <ConditionalCheckmark
              condition={scoreBreakdown.red.mobilityRobot1 === 'Yes'}
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.mobilityRobot2 === 'Yes'}
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.mobilityRobot3 === 'Yes'}
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
          </TableCell>
          <TableCell className="bg-gray-200">Mobility</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.mobilityRobot1 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.mobilityRobot2 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.mobilityRobot3 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
          </TableCell>
        </TableRow>

        {/* Auto Game Piece Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoGamePieceCount}
          </TableCell>
          <TableCell className="bg-gray-50">Auto Game Piece Count</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoGamePieceCount}
          </TableCell>
        </TableRow>

        {/* Auto Game Piece Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoGamePiecePoints}
          </TableCell>
          <TableCell className="bg-gray-200">Auto Game Piece Points</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoGamePiecePoints}
          </TableCell>
        </TableRow>

        {/* Charge Station Auto */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoChargeStationRobot1 === 'Docked' && (
              <Badge variant={'outline'}>
                {match.alliances.red.team_keys[0].substring(3)}
              </Badge>
            )}
            {scoreBreakdown.red.autoChargeStationRobot2 === 'Docked' && (
              <Badge variant={'outline'}>
                {match.alliances.red.team_keys[1].substring(3)}
              </Badge>
            )}
            {scoreBreakdown.red.autoChargeStationRobot3 === 'Docked' && (
              <Badge variant={'outline'}>
                {match.alliances.red.team_keys[2].substring(3)}
              </Badge>
            )}
          </TableCell>
          <TableCell className="bg-gray-50">Charge Station Auto</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoChargeStationRobot1 === 'Docked' && (
              <Badge variant={'outline'}>
                {match.alliances.blue.team_keys[0].substring(3)}
              </Badge>
            )}
            {scoreBreakdown.blue.autoChargeStationRobot2 === 'Docked' && (
              <Badge variant={'outline'}>
                {match.alliances.blue.team_keys[1].substring(3)}
              </Badge>
            )}
            {scoreBreakdown.blue.autoChargeStationRobot3 === 'Docked' && (
              <Badge variant={'outline'}>
                {match.alliances.blue.team_keys[2].substring(3)}
              </Badge>
            )}
          </TableCell>
        </TableRow>

        {/* Total Auto */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Total Auto</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoPoints}
          </TableCell>
        </TableRow>

        {/* Game Piece Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopGamePieceCount}
          </TableCell>
          <TableCell className="bg-gray-50">Game Piece Count</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopGamePieceCount}
          </TableCell>
        </TableRow>

        {/* Supercharged Nodes */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.extraGamePieceCount}
          </TableCell>
          <TableCell className="bg-gray-50">Supercharged Node</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.extraGamePieceCount}
          </TableCell>
        </TableRow>

        {/* Game Piece Points */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopGamePiecePoints}
          </TableCell>
          <TableCell className="bg-gray-200">Game Piece Points</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopGamePiecePoints}
          </TableCell>
        </TableRow>

        {/* Robot 1 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameChargeStationRobot1}
              teamKey={match.alliances.red.team_keys[0]}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 1 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameChargeStationRobot1}
              teamKey={match.alliances.blue.team_keys[0]}
            />
          </TableCell>
        </TableRow>

        {/* Robot 2 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameChargeStationRobot2}
              teamKey={match.alliances.red.team_keys[1]}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 2 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameChargeStationRobot2}
              teamKey={match.alliances.blue.team_keys[1]}
            />
          </TableCell>
        </TableRow>

        {/* Robot 3 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameChargeStationRobot3}
              teamKey={match.alliances.red.team_keys[2]}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 3 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameChargeStationRobot3}
              teamKey={match.alliances.blue.team_keys[2]}
            />
          </TableCell>
        </TableRow>

        {/* Total Teleop */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Total Teleop</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopPoints}
          </TableCell>
        </TableRow>

        {/* Links */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.links?.length} (+{scoreBreakdown.red.linkPoints}
            )
          </TableCell>
          <TableCell className="bg-gray-50">Links</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.links?.length} (+
            {scoreBreakdown.blue.linkPoints})
          </TableCell>
        </TableRow>

        {/* Coopertition Criteria Met */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.coopertitionCriteriaMet ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">
            Coopertition Criteria Met
          </TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.coopertitionCriteriaMet ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Sustainability Bonus */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={
                scoreBreakdown.red.sustainabilityBonusAchieved ?? false
              }
            />
          </TableCell>
          <TableCell className="bg-gray-50">Sustainability Bonus</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={
                scoreBreakdown.blue.sustainabilityBonusAchieved ?? false
              }
            />
          </TableCell>
        </TableRow>

        {/* Activation Bonus */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.activationBonusAchieved ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Activation Bonus</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.activationBonusAchieved ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Fouls / Tech Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.red.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2023]}
              techFoulsReceived={scoreBreakdown.red.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2023]}
              techOrMajor="tech"
            />
          </TableCell>
          <TableCell className="bg-gray-50">Fouls / Tech Fouls</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <FoulDisplay
              foulsReceived={scoreBreakdown.blue.foulCount}
              pointsPerFoul={POINTS_PER_FOUL[2023]}
              techFoulsReceived={scoreBreakdown.blue.techFoulCount}
              pointsPerTechFoul={POINTS_PER_TECH_FOUL[2023]}
              techOrMajor="tech"
            />
          </TableCell>
        </TableRow>

        {/* Adjustments */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.adjustPoints}
          </TableCell>
          <TableCell className="bg-gray-50">Adjustments</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.adjustPoints}
          </TableCell>
        </TableRow>

        {/* Total Score */}
        <TableRow className="font-bold">
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.totalPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Total Score</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.totalPoints}
          </TableCell>
        </TableRow>

        {/* RP */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            +{scoreBreakdown.red.rp} RP
          </TableCell>
          <TableCell className="bg-gray-50">RP</TableCell>
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
  endgame: MatchScoreBreakdown2023['red']['endGameChargeStationRobot1'];
  teamKey: string;
}) {
  const pointMap: Record<
    NonNullable<MatchScoreBreakdown2023['red']['endGameChargeStationRobot1']>,
    number
  > = {
    Docked: 10,
    Parked: 2,
    Park: 2,
    None: 0,
  };
  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant={'outline'}>{teamKey.substring(3)}</Badge>
      {endgame} (+{pointMap[endgame ?? 'None']})
    </div>
  );
}
