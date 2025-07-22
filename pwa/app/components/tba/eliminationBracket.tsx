import React, { useState } from 'react';
import { Link } from 'react-router';

import PlayCircle from '~icons/bi/play-circle';

import { EliminationAlliance, Event, Match } from '~/api/tba/read';
import { TeamLink } from '~/components/tba/links';
import { EventType } from '~/lib/api/EventType';

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

  // Helper to get division shortform (e.g., "Newton Division" -> "New")
  const getDivisionShortform = (divisionName: string): string => {
    // Common division names and their shortforms
    const divisionShortforms: Record<string, string> = {
      Newton: 'New',
      Einstein: 'Ein',
      Curie: 'Cur',
      Galileo: 'Gal',
      Hopper: 'Hop',
      Tesla: 'Tes',
      Turing: 'Tur',
      Archimedes: 'Arc',
      Carson: 'Car',
      Carver: 'Crv',
      Daly: 'Dal',
      Darwin: 'Dar',
      Johnson: 'Joh',
      Milstein: 'Mil',
      Roebling: 'Roe',
    };

    // Try to match the division name
    for (const [fullName, shortForm] of Object.entries(divisionShortforms)) {
      if (divisionName.includes(fullName)) {
        return shortForm;
      }
    }

    // If no match found, take first 3 letters
    return divisionName.substring(0, 3);
  };

  // Helper to get alliance display name
  const getAllianceDisplayName = (allianceNumber: number): string => {
    if (!allianceNumber || allianceNumber > alliances.length) return '';

    const alliance = alliances[allianceNumber - 1];
    if (isEinsteinEvent && alliance.name) {
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
  const matchesBySet = matches.reduce(
    (acc, match) => {
      if (!acc[match.set_number]) acc[match.set_number] = [];
      acc[match.set_number].push(match);
      return acc;
    },
    {} as Record<number, Match[]>,
  );

  // Helper to get first match video URL
  const maybeGetFirstMatchVideoURL = (match: Match): string | undefined => {
    if (match.videos.length === 0) {
      return undefined;
    }
    return `https://www.youtube.com/watch?v=${match.videos[0].key}`;
  };

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

    // For series, count wins (not used in this function but kept for potential future use)

    const matchPlayed =
      firstMatch.alliances.red.score !== -1 &&
      firstMatch.alliances.blue.score !== -1;

    return {
      redTeams,
      blueTeams,
      redAllianceNumber,
      blueAllianceNumber,
      redScore: firstMatch.alliances.red.score, // Always show actual match score
      blueScore: firstMatch.alliances.blue.score, // Always show actual match score
      redWon:
        firstMatch.alliances.red.score > firstMatch.alliances.blue.score &&
        matchPlayed,
      blueWon:
        firstMatch.alliances.blue.score > firstMatch.alliances.red.score &&
        matchPlayed,
      matchPlayed,
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
        className={`mb-2 min-w-fit rounded border border-gray-300 bg-white
          transition-all duration-200 ${
            isHighlighted ? 'shadow-lg ring-2 ring-yellow-400' : ''
          }`}
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
                  className={`text-red-600 transition-all duration-200 ${
                    isRedHighlighted ? 'rounded bg-red-100 px-1 text-sm' : ''
                  }`}
                >
                  {getAllianceDisplayName(result.redAllianceNumber)}
                </span>{' '}
                vs{' '}
                <span
                  className={`text-blue-600 transition-all duration-200 ${
                    isBlueHighlighted ? 'rounded bg-blue-100 px-1 text-sm' : ''
                  }`}
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
              const videoURL = maybeGetFirstMatchVideoURL(setMatches[0]);
              return videoURL ? (
                <Link
                  to={videoURL}
                  className="text-gray-600 hover:text-gray-800"
                >
                  <PlayCircle className="inline h-4 w-4" />
                </Link>
              ) : null;
            }
            return null;
          })()}
        </div>
        <div
          className={`flex cursor-pointer items-center justify-between
            bg-alliance-red-light px-1 py-1 transition-colors duration-200 ${
              isRedHighlighted ? 'bg-red-300' : 'hover:bg-red-200'
            }`}
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
                    className={`text-sm ${result.redWon ? 'font-bold' : ''} w-12
                    text-left text-red-600 ${
                      showUnderlines && teamPlayed
                        ? 'underline decoration-red-600 decoration-dotted'
                        : ''
                    }`}
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
            <span className={`text-sm ${result.redWon ? 'font-bold' : ''}`}>
              {result.redScore}
            </span>
          </div>
        </div>
        <div
          className={`flex cursor-pointer items-center justify-between
            bg-alliance-blue-light px-1 py-1 transition-colors duration-200 ${
              isBlueHighlighted ? 'bg-blue-300' : 'hover:bg-blue-200'
            }`}
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
                    className={`text-sm ${result.blueWon ? 'font-bold' : ''}
                    w-12 text-left text-blue-600 ${
                      showUnderlines && teamPlayed
                        ? 'underline decoration-blue-600 decoration-dotted'
                        : ''
                    }`}
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
            <span className={`text-sm ${result.blueWon ? 'font-bold' : ''}`}>
              {result.blueScore}
            </span>
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
        if (match.alliances.red.score > match.alliances.blue.score) {
          redWins++;
        } else if (match.alliances.blue.score > match.alliances.red.score) {
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
        className={`mb-2 min-w-fit rounded border border-gray-300 bg-white
          transition-all duration-200 ${
            isHighlighted ? 'shadow-lg ring-2 ring-yellow-400' : ''
          }`}
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
                  className={`text-red-600 transition-all duration-200 ${
                    isRedHighlighted ? 'rounded bg-red-100 px-1 text-sm' : ''
                  }`}
                >
                  {getAllianceDisplayName(redAllianceNumber)}
                </span>{' '}
                vs{' '}
                <span
                  className={`text-blue-600 transition-all duration-200 ${
                    isBlueHighlighted ? 'rounded bg-blue-100 px-1 text-sm' : ''
                  }`}
                >
                  {getAllianceDisplayName(blueAllianceNumber)}
                </span>
                )
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {finalsMatches.map((match, idx) => {
              const videoURL = maybeGetFirstMatchVideoURL(match);
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
          className={`flex cursor-pointer items-center justify-between
            bg-alliance-red-light px-1 py-1 transition-colors duration-200 ${
              isRedHighlighted ? 'bg-red-300' : 'hover:bg-red-200'
            }`}
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
                    className={`text-sm ${redWonSeries ? 'font-bold' : ''} w-12
                    text-left text-red-600 ${
                      showUnderlines && teamPlayed
                        ? 'underline decoration-red-600 decoration-dotted'
                        : ''
                    }`}
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
                  className={`text-sm
                  ${match.alliances.red.score > match.alliances.blue.score ? 'font-bold' : ''}
                  w-8 flex-shrink-0 text-center`}
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
          className={`flex cursor-pointer items-center justify-between
            bg-alliance-blue-light px-1 py-1 transition-colors duration-200 ${
              isBlueHighlighted ? 'bg-blue-300' : 'hover:bg-blue-200'
            }`}
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
                    className={`text-sm ${blueWonSeries ? 'font-bold' : ''} w-12
                    text-left text-blue-600 ${
                      showUnderlines && teamPlayed
                        ? 'underline decoration-blue-600 decoration-dotted'
                        : ''
                    }`}
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
                  className={`text-sm
                  ${match.alliances.blue.score > match.alliances.red.score ? 'font-bold' : ''}
                  w-8 flex-shrink-0 text-center`}
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
          className="relative flex min-w-max items-start justify-start gap-8
            px-4"
        >
          {/* Left Side: Upper and Lower Brackets */}
          <div className="space-y-4">
            {/* Upper Bracket */}
            <div className="space-y-4">
              <h2 className="text-center text-xl font-bold">Upper Bracket</h2>
              <div className="flex items-start gap-6">
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
              <div className="flex items-start gap-6">
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
          <div className="flex flex-col items-center">
            <h3 className="mb-4 text-center font-bold">Finals</h3>
            <div className="space-y-4">
              <div className="h-48"></div>
              {renderFinalsSection()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
