import BiVolumeMute from '~icons/bi/volume-mute';
import BiVolumeUp from '~icons/bi/volume-up';

import { Match, MatchScoreBreakdown2024 } from '~/api/tba/read';
import InlineIcon from '~/components/tba/inlineIcon';
import {
  ConditionalCheckmark,
  ConditionalRpAchieved,
} from '~/components/tba/match/common';
import { Badge } from '~/components/ui/badge';
import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';

export default function ScoreBreakdown2024({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2024;
  match: Match;
}) {
  return (
    <Table className="table-fixed text-center">
      <colgroup>
        <col />
        <col className="w-[45%]" />
        <col />
      </colgroup>
      <TableBody>
        {/* Auto Leave */}
        <TableRow>
          <TableCell
            className="bg-alliance-red-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.red.autoLineRobot1 === 'Yes'}
              teamKey={match.alliances.red.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.autoLineRobot2 === 'Yes'}
              teamKey={match.alliances.red.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.red.autoLineRobot3 === 'Yes'}
              teamKey={match.alliances.red.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.red.autoLeavePoints})
          </TableCell>
          <TableCell className="bg-gray-200">Auto Leave</TableCell>
          <TableCell
            className="bg-alliance-blue-dark whitespace-nowrap *:align-middle"
          >
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.autoLineRobot1 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[0].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.autoLineRobot2 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[1].substring(3)}
            />
            <ConditionalCheckmark
              condition={scoreBreakdown.blue.autoLineRobot3 === 'Yes'}
              teamKey={match.alliances.blue.team_keys[2].substring(3)}
            />
            (+{scoreBreakdown.blue.autoLeavePoints})
          </TableCell>
        </TableRow>

        {/* Auto Amp Note Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoAmpNoteCount}
          </TableCell>
          <TableCell className="bg-gray-50">Auto Amp Note Count</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoAmpNoteCount}
          </TableCell>
        </TableRow>

        {/* Auto Speaker Note Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.autoSpeakerNoteCount}
          </TableCell>
          <TableCell className="bg-gray-50">Auto Speaker Note Count</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.autoSpeakerNoteCount}
          </TableCell>
        </TableRow>

        {/* Auto Note Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.autoTotalNotePoints}
          </TableCell>
          <TableCell className="bg-gray-200">Auto Note Points</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.autoTotalNotePoints}
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

        {/* Teleop Amp Note Count */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.teleopAmpNoteCount}
          </TableCell>
          <TableCell className="bg-gray-50">Teleop Amp Note Count</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.teleopAmpNoteCount}
          </TableCell>
        </TableRow>

        {/* Teleop Speaker Note Count */}
        <TableRow>
          <TableCell
            className="flex flex-row items-center justify-center gap-4
              bg-alliance-red-light"
          >
            <InlineIcon>
              <BiVolumeUp className="size-4" />
              {scoreBreakdown.red.teleopSpeakerNoteAmplifiedCount}
            </InlineIcon>
            <InlineIcon>
              <BiVolumeMute className="size-4" />
              {scoreBreakdown.red.teleopSpeakerNoteCount}
            </InlineIcon>
          </TableCell>
          <TableCell className="bg-gray-50">
            Teleop Speaker Note Count
          </TableCell>

          <TableCell
            className="flex flex-row items-center justify-center gap-4
              bg-alliance-blue-light"
          >
            <InlineIcon>
              <BiVolumeUp className="size-4" />
              {scoreBreakdown.blue.teleopSpeakerNoteAmplifiedCount}
            </InlineIcon>
            <InlineIcon>
              <BiVolumeMute className="size-4" />
              {scoreBreakdown.blue.teleopSpeakerNoteCount}
            </InlineIcon>
          </TableCell>
        </TableRow>

        {/* Teleop Note Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.teleopTotalNotePoints}
          </TableCell>
          <TableCell className="bg-gray-200">Teleop Note Points</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.teleopTotalNotePoints}
          </TableCell>
        </TableRow>

        {/* Robot 1 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameRobot1}
              teamKey={match.alliances.red.team_keys[0]}
              trapCenterStage={scoreBreakdown.red.trapCenterStage ?? false}
              trapStageLeft={scoreBreakdown.red.trapStageLeft ?? false}
              trapStageRight={scoreBreakdown.red.trapStageRight ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 1 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameRobot1}
              teamKey={match.alliances.blue.team_keys[0]}
              trapCenterStage={scoreBreakdown.blue.trapCenterStage ?? false}
              trapStageLeft={scoreBreakdown.blue.trapStageLeft ?? false}
              trapStageRight={scoreBreakdown.blue.trapStageRight ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Robot 2 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameRobot2}
              teamKey={match.alliances.red.team_keys[1]}
              trapCenterStage={scoreBreakdown.red.trapCenterStage ?? false}
              trapStageLeft={scoreBreakdown.red.trapStageLeft ?? false}
              trapStageRight={scoreBreakdown.red.trapStageRight ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 2 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameRobot2}
              teamKey={match.alliances.blue.team_keys[1]}
              trapCenterStage={scoreBreakdown.blue.trapCenterStage ?? false}
              trapStageLeft={scoreBreakdown.blue.trapStageLeft ?? false}
              trapStageRight={scoreBreakdown.blue.trapStageRight ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Robot 3 Endgame */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.red.endGameRobot3}
              teamKey={match.alliances.red.team_keys[2]}
              trapCenterStage={scoreBreakdown.red.trapCenterStage ?? false}
              trapStageLeft={scoreBreakdown.red.trapStageLeft ?? false}
              trapStageRight={scoreBreakdown.red.trapStageRight ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Robot 3 Endgame</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <EndgameRobotCell
              endgame={scoreBreakdown.blue.endGameRobot3}
              teamKey={match.alliances.blue.team_keys[2]}
              trapCenterStage={scoreBreakdown.blue.trapCenterStage ?? false}
              trapStageLeft={scoreBreakdown.blue.trapStageLeft ?? false}
              trapStageRight={scoreBreakdown.blue.trapStageRight ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Harmony Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.endGameHarmonyPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Harmony Points</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.endGameHarmonyPoints}
          </TableCell>
        </TableRow>

        {/* Trap Points */}
        <TableRow>
          <TableCell className="bg-alliance-red-dark">
            {scoreBreakdown.red.endGameNoteInTrapPoints}
          </TableCell>
          <TableCell className="bg-gray-200">Trap Points</TableCell>
          <TableCell className="bg-alliance-blue-dark">
            {scoreBreakdown.blue.endGameNoteInTrapPoints}
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

        {/* Melody Bonus */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.red.melodyBonusAchieved ?? false}
            />
          </TableCell>
          <TableCell className="bg-gray-50">Melody Bonus</TableCell>
          <TableCell className="bg-alliance-blue-light">
            <ConditionalRpAchieved
              condition={scoreBreakdown.blue.melodyBonusAchieved ?? false}
            />
          </TableCell>
        </TableRow>

        {/* Fouls / Tech Fouls */}
        <TableRow>
          <TableCell className="bg-alliance-red-light">
            {scoreBreakdown.red.foulCount} (+
            {(scoreBreakdown.red.foulCount ?? 0) * 2}) /{' '}
            {scoreBreakdown.red.techFoulCount} (+
            {(scoreBreakdown.red.techFoulCount ?? 0) * 5})
          </TableCell>
          <TableCell className="bg-gray-50">Fouls / Tech Fouls</TableCell>
          <TableCell className="bg-alliance-blue-light">
            {scoreBreakdown.blue.foulCount} (+
            {(scoreBreakdown.blue.foulCount ?? 0) * 2}) /{' '}
            {scoreBreakdown.blue.techFoulCount} (+
            {(scoreBreakdown.blue.techFoulCount ?? 0) * 5})
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
  trapCenterStage,
  trapStageLeft,
  trapStageRight,
}: {
  endgame: MatchScoreBreakdown2024['red']['endGameRobot1'];
  trapCenterStage: boolean;
  trapStageLeft: boolean;
  trapStageRight: boolean;
  teamKey: string;
}) {
  let display = 'None';
  let points = 0;

  if (
    (endgame === 'CenterStage' && trapCenterStage) ||
    (endgame === 'StageLeft' && trapStageLeft) ||
    (endgame === 'StageRight' && trapStageRight)
  ) {
    display = 'Spotlit';
    points = 4;
  } else {
    const pointMap: Record<
      NonNullable<MatchScoreBreakdown2024['red']['endGameRobot1']>,
      number
    > = {
      StageLeft: 3,
      StageRight: 3,
      CenterStage: 3,
      Parked: 1,
      None: 0,
    };

    const displayMap: Record<
      NonNullable<MatchScoreBreakdown2024['red']['endGameRobot1']>,
      string
    > = {
      StageLeft: 'Onstage',
      StageRight: 'Onstage',
      CenterStage: 'Onstage',
      Parked: 'Parked',
      None: 'None',
    };

    display = displayMap[endgame ?? 'None'];
    points = pointMap[endgame ?? 'None'];
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <Badge variant={'outline'}>{teamKey.substring(3)}</Badge>
      {display} (+{points})
    </div>
  );
}
