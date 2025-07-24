import React, { useState } from 'react';
import { Link } from 'react-router';

import PlayCircle from '~icons/bi/play-circle';

import { EliminationAlliance, Event, Match } from '~/api/tba/read';
import { TeamLink } from '~/components/tba/links';
import { EventType } from '~/lib/api/EventType';
import { getDivisionShortform } from '~/lib/eventUtils';
import { maybeGetFirstMatchVideoURL } from '~/lib/matchUtils';
import { cn } from '~/lib/utils';

export interface EliminationBracketProps {
  alliances: EliminationAlliance[];
  matches: Match[];
  year?: number;
  event?: Event;
}

export default function EliminationBracket({
  alliances,
  matches,
  year,
  event,
}: EliminationBracketProps): React.JSX.Element {
  const [hoveredAlliance, setHoveredAlliance] = useState<number | null>(null);

  // Check if this is an Einstein event (CMP_FINALS)
  const isEinsteinEvent = event?.event_type === EventType.CMP_FINALS;

  // Helper to get alliance display name
  const getAllianceDisplayName = (allianceNumber: number): string => {
    if (!allianceNumber || allianceNumber > alliances.length) return '';

    const alliance = alliances[allianceNumber - 1];
    if (isEinsteinEvent && alliance.name && typeof alliance.name === 'string') {
      // For Einstein events, use division shortform if available
      return getDivisionShortform(alliance.name);
    }
    // Default to alliance number
    return `#${allianceNumber}`;
  };

  if (
    !alliances ||
    alliances.length === 0 ||
    !matches ||
    matches.length === 0
  ) {
    return <div></div>;
  }

  // Group matches by set_number
  const matchesBySet: Record<number, Match[]> = matches.reduce(
    (acc, match) => {
      if (!acc[match.set_number]) acc[match.set_number] = [];
      acc[match.set_number].push(match);
      return acc;
    },
    {} as Record<number, Match[]>,
  );

  // Helper to get alliance numbers for teams
  const getAllianceNumber = (teamKeys: string[]) => {
    for (let i = 0; i < alliances.length; i++) {
      const alliance = alliances[i];
      // Check if all team keys match this alliance
      const allianceTeamKeys = alliance.picks.map((pick) => pick.substring(3));
      if (teamKeys.every((team) => allianceTeamKeys.includes(team))) {
        return i + 1; // Alliance numbers are 1-based
      }
    }
    return null;
  };

  // Helper to get match result
  const getMatchResult = (setNumber: number) => {
    const setMatches = matchesBySet[setNumber];
    if (!setMatches || setMatches.length === 0) return null;

    // Sort matches by match number to get them in order
    const sortedMatches = [...setMatches].sort(
      (a, b) => a.match_number - b.match_number,
    );

    // Use the first match to get team information (they should be the same across the series)
    const firstMatch = sortedMatches[0];
    const matchRedTeams = firstMatch.alliances.red.team_keys.map((t) =>
      t.substring(3),
    );
    const matchBlueTeams = firstMatch.alliances.blue.team_keys.map((t) =>
      t.substring(3),
    );

    // Get alliance numbers and full alliance rosters
    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);

    // Get full alliance rosters (all teams, not just the 3 that played)
    const redTeams = redAllianceNumber
      ? alliances[redAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchRedTeams;
    const blueTeams = blueAllianceNumber
      ? alliances[blueAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchBlueTeams;

    // Check if first match is a true tie
    const firstMatchPlayed =
      firstMatch.alliances.red.score !== -1 &&
      firstMatch.alliances.blue.score !== -1;
    const isFirstMatchTie =
      firstMatchPlayed && firstMatch.winning_alliance === '';

    // For true ties, show both matches if second match exists
    const showBothMatches = isFirstMatchTie && sortedMatches.length > 1;
    const secondMatch = showBothMatches ? sortedMatches[1] : null;

    const matchPlayed = firstMatchPlayed;

    // Determine overall winner from the series
    let redWon = false;
    let blueWon = false;

    if (showBothMatches && secondMatch) {
      const secondMatchPlayed =
        secondMatch.alliances.red.score !== -1 &&
        secondMatch.alliances.blue.score !== -1;
      if (secondMatchPlayed) {
        redWon = secondMatch.winning_alliance === 'red';
        blueWon = secondMatch.winning_alliance === 'blue';
      }
    } else {
      redWon = firstMatch.winning_alliance === 'red' && matchPlayed;
      blueWon = firstMatch.winning_alliance === 'blue' && matchPlayed;
    }

    return {
      redTeams,
      blueTeams,
      redAllianceNumber,
      blueAllianceNumber,
      redScore: firstMatch.alliances.red.score, // First match score
      blueScore: firstMatch.alliances.blue.score, // First match score
      redScore2: secondMatch?.alliances.red.score ?? null, // Second match score
      blueScore2: secondMatch?.alliances.blue.score ?? null, // Second match score
      redWon,
      blueWon,
      matchPlayed,
      showBothMatches,
      matchRedTeams, // Teams that actually played
      matchBlueTeams, // Teams that actually played
    };
  };

  // Helper to render a match
  const renderMatch = (setNumber: number, matchLabel: string) => {
    const result = getMatchResult(setNumber);
    if (!result) return null;

    const isRedHighlighted = hoveredAlliance === result.redAllianceNumber;
    const isBlueHighlighted = hoveredAlliance === result.blueAllianceNumber;
    const isHighlighted = isRedHighlighted || isBlueHighlighted;

    return (
      <div
        className={cn(
          `mb-2 min-w-[180px] rounded border border-gray-300 bg-white
          transition-all duration-200`,
          isHighlighted && 'shadow-lg ring-2 ring-yellow-400',
        )}
      >
        <div
          className="flex items-center justify-between border-b bg-gray-100 px-2
            py-1 text-sm font-bold"
        >
          <div className="flex items-center gap-1">
            <span>{matchLabel}</span>
            {result.redAllianceNumber && result.blueAllianceNumber && (
              <span className="text-xs font-normal">
                (
                <span
                  className={cn(
                    'text-red-600 transition-all duration-200',
                    isRedHighlighted && 'rounded bg-red-100 px-1 text-sm',
                  )}
                >
                  {getAllianceDisplayName(result.redAllianceNumber)}
                </span>{' '}
                vs{' '}
                <span
                  className={cn(
                    'text-blue-600 transition-all duration-200',
                    isBlueHighlighted && 'rounded bg-blue-100 px-1 text-sm',
                  )}
                >
                  {getAllianceDisplayName(result.blueAllianceNumber)}
                </span>
                )
              </span>
            )}
          </div>
          {(() => {
            const setMatches = matchesBySet[setNumber];
            if (setMatches && setMatches.length > 0) {
              const firstMatch: Match | undefined = setMatches[0];
              if (firstMatch) {
                const videoURL: string | undefined =
                  maybeGetFirstMatchVideoURL(firstMatch);
                if (videoURL) {
                  return (
                    <Link
                      to={videoURL}
                      className="text-gray-600 hover:text-gray-800"
                    >
                      <PlayCircle className="inline h-4 w-4" />
                    </Link>
                  );
                }
              }
            }
            return null;
          })()}
        </div>
        <div
          className={cn(
            `flex cursor-pointer items-center justify-between
            bg-alliance-red-light px-1 py-1 transition-colors duration-200`,
            isRedHighlighted ? 'bg-red-300' : 'hover:bg-red-200',
          )}
          onMouseEnter={() =>
            result.redAllianceNumber &&
            setHoveredAlliance(result.redAllianceNumber)
          }
          onMouseLeave={() => setHoveredAlliance(null)}
        >
          <div className="flex flex-1 items-center justify-start">
            <div className="flex">
              {result.redTeams.map((team) => {
                const teamPlayed = result.matchRedTeams.includes(team);
                const showUnderlines = result.redTeams.length > 3; // Only show underlines if there are backup teams
                return (
                  <span
                    key={team}
                    className={cn(
                      'w-10 text-left text-sm text-red-600',
                      result.redWon && 'font-bold',
                      showUnderlines &&
                        teamPlayed &&
                        'underline decoration-red-600 decoration-dotted',
                    )}
                  >
                    <TeamLink teamOrKey={`frc${team}`} year={year}>
                      {team}
                    </TeamLink>
                  </span>
                );
              })}
            </div>
          </div>
          <div className="flex items-center">
            {result.showBothMatches ? (
              <div className="flex min-w-0 gap-1">
                <span
                  className="w-8 flex-shrink-0 text-center text-sm underline
                    decoration-dotted decoration-2 [&:hover]:delay-0"
                  title="True tie"
                >
                  {result.redScore}
                </span>
                <span
                  className={cn(
                    'w-8 flex-shrink-0 text-center text-sm',
                    result.redWon && 'font-bold',
                  )}
                >
                  {result.redScore2}
                </span>
              </div>
            ) : (
              <span className={cn('text-sm', result.redWon && 'font-bold')}>
                {result.redScore}
              </span>
            )}
          </div>
        </div>
        <div
          className={cn(
            `flex cursor-pointer items-center justify-between
            bg-alliance-blue-light px-1 py-1 transition-colors duration-200`,
            isBlueHighlighted ? 'bg-blue-300' : 'hover:bg-blue-200',
          )}
          onMouseEnter={() =>
            result.blueAllianceNumber &&
            setHoveredAlliance(result.blueAllianceNumber)
          }
          onMouseLeave={() => setHoveredAlliance(null)}
        >
          <div className="flex flex-1 items-center justify-start">
            <div className="flex">
              {result.blueTeams.map((team) => {
                const teamPlayed = result.matchBlueTeams.includes(team);
                const showUnderlines = result.blueTeams.length > 3; // Only show underlines if there are backup teams
                return (
                  <span
                    key={team}
                    className={cn(
                      'w-10 text-left text-sm text-blue-600',
                      result.blueWon && 'font-bold',
                      showUnderlines &&
                        teamPlayed &&
                        'underline decoration-blue-600 decoration-dotted',
                    )}
                  >
                    <TeamLink teamOrKey={`frc${team}`} year={year}>
                      {team}
                    </TeamLink>
                  </span>
                );
              })}
            </div>
          </div>
          <div className="flex items-center">
            {result.showBothMatches ? (
              <div className="flex min-w-0 gap-1">
                <span
                  className="w-8 flex-shrink-0 text-center text-sm underline
                    decoration-dotted decoration-2 [&:hover]:delay-0"
                  title="True tie"
                >
                  {result.blueScore}
                </span>
                <span
                  className={cn(
                    'w-8 flex-shrink-0 text-center text-sm',
                    result.blueWon && 'font-bold',
                  )}
                >
                  {result.blueScore2}
                </span>
              </div>
            ) : (
              <span className={cn('text-sm', result.blueWon && 'font-bold')}>
                {result.blueScore}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Special finals renderer showing individual match scores in columns
  const renderFinalsSection = () => {
    const finalsMatches = matches
      .filter((m) => m.comp_level === 'f')
      .sort((a, b) => a.match_number - b.match_number);
    if (finalsMatches.length === 0) return null;

    // Get the two competing alliances from the first finals match
    const firstMatch = finalsMatches[0];
    if (!firstMatch) return null;

    const matchRedTeams = firstMatch.alliances.red.team_keys.map((t) =>
      t.substring(3),
    );
    const matchBlueTeams = firstMatch.alliances.blue.team_keys.map((t) =>
      t.substring(3),
    );

    // Get alliance numbers and full alliance rosters
    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);

    // Get full alliance rosters (all teams, not just the 3 that played)
    const redTeams = redAllianceNumber
      ? alliances[redAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchRedTeams;
    const blueTeams = blueAllianceNumber
      ? alliances[blueAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchBlueTeams;

    // Calculate total wins for each alliance
    let redWins = 0;
    let blueWins = 0;

    finalsMatches.forEach((match) => {
      if (
        match.alliances.red.score !== -1 &&
        match.alliances.blue.score !== -1
      ) {
        if (match.winning_alliance === 'red') {
          redWins++;
        } else if (match.winning_alliance === 'blue') {
          blueWins++;
        }
      }
    });

    const redWonSeries = redWins > blueWins;
    const blueWonSeries = blueWins > redWins;

    const isRedHighlighted = hoveredAlliance === redAllianceNumber;
    const isBlueHighlighted = hoveredAlliance === blueAllianceNumber;
    const isHighlighted = isRedHighlighted || isBlueHighlighted;

    return (
      <div
        className={cn(
          `mb-2 min-w-[180px] rounded border border-gray-300 bg-white
          transition-all duration-200`,
          isHighlighted && 'shadow-lg ring-2 ring-yellow-400',
        )}
      >
        <div
          className="flex items-center justify-between border-b bg-gray-100 px-2
            py-1 text-sm font-bold"
        >
          <div className="flex items-center gap-1">
            <span>Finals</span>
            {redAllianceNumber && blueAllianceNumber && (
              <span className="text-xs font-normal">
                (
                <span
                  className={cn(
                    'text-red-600 transition-all duration-200',
                    isRedHighlighted && 'rounded bg-red-100 px-1 text-sm',
                  )}
                >
                  {getAllianceDisplayName(redAllianceNumber)}
                </span>{' '}
                vs{' '}
                <span
                  className={cn(
                    'text-blue-600 transition-all duration-200',
                    isBlueHighlighted && 'rounded bg-blue-100 px-1 text-sm',
                  )}
                >
                  {getAllianceDisplayName(blueAllianceNumber)}
                </span>
                )
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {finalsMatches.map((match, idx) => {
              const videoURL: string | undefined =
                maybeGetFirstMatchVideoURL(match);
              return videoURL ? (
                <Link
                  key={idx}
                  to={videoURL}
                  className="flex w-8 items-center justify-center text-gray-600
                    hover:text-gray-800"
                >
                  <PlayCircle className="inline h-4 w-4" />
                </Link>
              ) : (
                <div
                  key={idx}
                  className="flex h-4 w-8 items-center justify-center"
                ></div>
              );
            })}
          </div>
        </div>
        <div
          className={cn(
            `flex cursor-pointer items-center justify-between
            bg-alliance-red-light px-1 py-1 transition-colors duration-200`,
            isRedHighlighted ? 'bg-red-300' : 'hover:bg-red-200',
          )}
          onMouseEnter={() =>
            redAllianceNumber && setHoveredAlliance(redAllianceNumber)
          }
          onMouseLeave={() => setHoveredAlliance(null)}
        >
          <div className="flex flex-1 items-center justify-start">
            <div className="flex">
              {redTeams.map((team) => {
                const teamPlayed = matchRedTeams.includes(team);
                const showUnderlines = redTeams.length > 3; // Only show underlines if there are backup teams
                return (
                  <span
                    key={team}
                    className={cn(
                      'w-10 text-left text-sm text-red-600',
                      redWonSeries && 'font-bold',
                      showUnderlines &&
                        teamPlayed &&
                        'underline decoration-red-600 decoration-dotted',
                    )}
                  >
                    <TeamLink teamOrKey={`frc${team}`} year={year}>
                      {team}
                    </TeamLink>
                  </span>
                );
              })}
            </div>
          </div>
          <div className="flex items-center">
            <div className="flex min-w-0 gap-1">
              {finalsMatches.map((match, idx) => (
                <span
                  key={idx}
                  className={cn(
                    'w-8 flex-shrink-0 text-center text-sm',
                    match.winning_alliance === 'red' && 'font-bold',
                  )}
                >
                  {match.alliances.red.score !== -1
                    ? match.alliances.red.score
                    : '-'}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div
          className={cn(
            `flex cursor-pointer items-center justify-between
            bg-alliance-blue-light px-1 py-1 transition-colors duration-200`,
            isBlueHighlighted ? 'bg-blue-300' : 'hover:bg-blue-200',
          )}
          onMouseEnter={() =>
            blueAllianceNumber && setHoveredAlliance(blueAllianceNumber)
          }
          onMouseLeave={() => setHoveredAlliance(null)}
        >
          <div className="flex flex-1 items-center justify-start">
            <div className="flex">
              {blueTeams.map((team) => {
                const teamPlayed = matchBlueTeams.includes(team);
                const showUnderlines = blueTeams.length > 3; // Only show underlines if there are backup teams
                return (
                  <span
                    key={team}
                    className={cn(
                      'w-10 text-left text-sm text-blue-600',
                      blueWonSeries && 'font-bold',
                      showUnderlines &&
                        teamPlayed &&
                        'underline decoration-blue-600 decoration-dotted',
                    )}
                  >
                    <TeamLink teamOrKey={`frc${team}`} year={year}>
                      {team}
                    </TeamLink>
                  </span>
                );
              })}
            </div>
          </div>
          <div className="flex items-center">
            <div className="flex min-w-0 gap-1">
              {finalsMatches.map((match, idx) => (
                <span
                  key={idx}
                  className={cn(
                    'w-8 flex-shrink-0 text-center text-sm',
                    match.winning_alliance === 'blue' && 'font-bold',
                  )}
                >
                  {match.alliances.blue.score !== -1
                    ? match.alliances.blue.score
                    : '-'}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="mt-8">
      <h2 className="mb-4 text-2xl font-bold">Playoff Bracket</h2>

      <div className="overflow-x-auto overflow-y-hidden">
        <div
          className="relative flex min-w-max items-start justify-start gap-6
            px-4"
        >
          {/* Left Side: Upper and Lower Brackets */}
          <div className="space-y-4">
            {/* Upper Bracket */}
            <div className="space-y-4">
              <h2 className="text-center text-xl font-bold">Upper Bracket</h2>
              <div className="flex items-start gap-4">
                {/* Round 1 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 1</h3>
                  <div className="space-y-4">
                    {renderMatch(1, 'Match 1')}
                    {renderMatch(2, 'Match 2')}
                    <div className="h-6"></div>
                    {renderMatch(3, 'Match 3')}
                    {renderMatch(4, 'Match 4')}
                  </div>
                </div>

                {/* Round 2 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 2</h3>
                  <div className="space-y-4">
                    <div className="h-4"></div>
                    {renderMatch(7, 'Match 7')}
                    <div className="h-28"></div>
                    {renderMatch(8, 'Match 8')}
                  </div>
                </div>

                {/* Round 4 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 4</h3>
                  <div className="space-y-4">
                    <div className="h-32"></div>
                    {renderMatch(11, 'Match 11')}
                  </div>
                </div>
              </div>
            </div>

            {/* Lower Bracket */}
            <div className="space-y-4">
              <h2 className="text-center text-xl font-bold">Lower Bracket</h2>
              <div className="flex items-start gap-4">
                {/* Round 2 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 2</h3>
                  <div className="space-y-4">
                    {renderMatch(5, 'Match 5')}
                    <div className="h-6"></div>
                    {renderMatch(6, 'Match 6')}
                  </div>
                </div>

                {/* Round 3 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 3</h3>
                  <div className="space-y-4">
                    {renderMatch(10, 'Match 10')}
                    <div className="h-6"></div>
                    {renderMatch(9, 'Match 9')}
                  </div>
                </div>

                {/* Round 4 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 4</h3>
                  <div className="space-y-4">
                    <div className="h-8"></div>
                    {renderMatch(12, 'Match 12')}
                  </div>
                </div>

                {/* Round 5 */}
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Round 5</h3>
                  <div className="space-y-4">
                    <div className="h-8"></div>
                    {renderMatch(13, 'Match 13')}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side: Grand Finals */}
          <div className="space-y-4">
            <div className="space-y-4">
              <h2 className="text-center text-xl font-bold">&nbsp;</h2>
              <div className="flex items-start gap-4">
                <div className="flex flex-col items-center">
                  <h3 className="mb-4 text-center font-bold">Finals</h3>
                  <div className="space-y-4">
                    <div className="h-32"></div>
                    {renderFinalsSection()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
