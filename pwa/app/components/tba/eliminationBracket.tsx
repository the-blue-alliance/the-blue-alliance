import React from 'react';
import { Link } from 'react-router';
import PlayCircle from '~icons/bi/play-circle';

import { EliminationAlliance, Match } from '~/api/tba/read';
import { TeamLink } from '~/components/tba/links';

export interface EliminationBracketProps {
  alliances: EliminationAlliance[];
  matches: Match[];
  year?: number;
}

export default function EliminationBracket({
  alliances,
  matches,
  year,
}: EliminationBracketProps): React.JSX.Element {
  if (!alliances || alliances.length === 0 || !matches || matches.length === 0) {
    return null;
  }

  // Group matches by set_number
  const matchesBySet = matches.reduce((acc, match) => {
    if (!acc[match.set_number]) acc[match.set_number] = [];
    acc[match.set_number].push(match);
    return acc;
  }, {} as Record<number, Match[]>);

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
      const allianceTeamKeys = alliance.picks.map(pick => pick.substring(3));
      if (teamKeys.every(team => allianceTeamKeys.includes(team))) {
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
    const sortedMatches = [...setMatches].sort((a, b) => a.match_number - b.match_number);
    
    // Use the first match to get team information (they should be the same across the series)
    const firstMatch = sortedMatches[0];
    const matchRedTeams = firstMatch.alliances.red.team_keys.map(t => t.substring(3));
    const matchBlueTeams = firstMatch.alliances.blue.team_keys.map(t => t.substring(3));
    
    // Get alliance numbers and full alliance rosters
    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);
    
    // Get full alliance rosters (all teams, not just the 3 that played)
    const redTeams = redAllianceNumber ? alliances[redAllianceNumber - 1].picks.map(pick => pick.substring(3)) : matchRedTeams;
    const blueTeams = blueAllianceNumber ? alliances[blueAllianceNumber - 1].picks.map(pick => pick.substring(3)) : matchBlueTeams;
    
    let redWins = 0;
    let blueWins = 0;
    
    // For series, count wins
    if (setMatches.length > 1) {
      setMatches.forEach(match => {
        if (match.alliances.red.score !== -1 && match.alliances.blue.score !== -1) {
          if (match.alliances.red.score > match.alliances.blue.score) {
            redWins++;
          } else {
            blueWins++;
          }
        }
      });
    } else {
      // For single matches, use actual scores
      if (firstMatch.alliances.red.score !== -1 && firstMatch.alliances.blue.score !== -1) {
        redWins = firstMatch.alliances.red.score;
        blueWins = firstMatch.alliances.blue.score;
      }
    }


    const redWon = setMatches.length > 1 ? redWins > blueWins : firstMatch.alliances.red.score > firstMatch.alliances.blue.score;
    const blueWon = setMatches.length > 1 ? blueWins > redWins : firstMatch.alliances.blue.score > firstMatch.alliances.red.score;
    const matchPlayed = firstMatch.alliances.red.score !== -1 && firstMatch.alliances.blue.score !== -1;

    return {
      redTeams,
      blueTeams,
      redAllianceNumber,
      blueAllianceNumber,
      redScore: firstMatch.alliances.red.score, // Always show actual match score
      blueScore: firstMatch.alliances.blue.score, // Always show actual match score
      redWon: firstMatch.alliances.red.score > firstMatch.alliances.blue.score && matchPlayed,
      blueWon: firstMatch.alliances.blue.score > firstMatch.alliances.red.score && matchPlayed,
      matchPlayed,
      matchRedTeams, // Teams that actually played
      matchBlueTeams // Teams that actually played
    };
  };

  // Helper to render a match
  const renderMatch = (setNumber: number, matchLabel: string) => {
    const result = getMatchResult(setNumber);
    if (!result) return null;

    return (
      <div className="border border-gray-300 rounded bg-white mb-2 w-64">
        <div className="bg-gray-100 px-2 py-1 text-sm font-bold border-b flex items-center justify-between">
          <span>{matchLabel}</span>
          {(() => {
            const setMatches = matchesBySet[setNumber];
            if (setMatches && setMatches.length > 0) {
              const videoURL = maybeGetFirstMatchVideoURL(setMatches[0]);
              return videoURL ? (
                <Link to={videoURL} className="text-gray-600 hover:text-gray-800">
                  <PlayCircle className="inline w-4 h-4" />
                </Link>
              ) : null;
            }
            return null;
          })()}
        </div>
        <div className="px-2 py-1 flex justify-between items-center bg-red-100">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-3">
              {result.redAllianceNumber && (
                <span className="text-sm font-semibold text-red-800">
                  #{result.redAllianceNumber}
                </span>
              )}
              <div className="flex gap-1">
                {result.redTeams.map((team, idx) => {
                  const teamPlayed = result.matchRedTeams.includes(team);
                  const showUnderlines = result.redTeams.length > 3; // Only show underlines if there are backup teams
                  return (
                    <TeamLink
                      key={team}
                      teamOrKey={`frc${team}`}
                      year={year}
                      className={`text-sm ${result.redWon ? 'font-bold' : ''} w-10 text-left text-red-600 ${
                        showUnderlines && teamPlayed ? 'underline decoration-dotted decoration-red-600' : ''
                      }`}
                    >
                      {team}
                    </TeamLink>
                  );
                })}
              </div>
            </div>
          </div>
          <span className={`text-sm ${result.redWon ? 'font-bold' : ''}`}>{result.redScore}</span>
        </div>
        <div className="px-2 py-1 flex justify-between items-center bg-blue-100">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-3">
              {result.blueAllianceNumber && (
                <span className="text-sm font-semibold text-blue-800">
                  #{result.blueAllianceNumber}
                </span>
              )}
              <div className="flex gap-1">
                {result.blueTeams.map((team, idx) => {
                  const teamPlayed = result.matchBlueTeams.includes(team);
                  const showUnderlines = result.blueTeams.length > 3; // Only show underlines if there are backup teams
                  return (
                    <TeamLink
                      key={team}
                      teamOrKey={`frc${team}`}
                      year={year}
                      className={`text-sm ${result.blueWon ? 'font-bold' : ''} w-10 text-left text-blue-600 ${
                        showUnderlines && teamPlayed ? 'underline decoration-dotted decoration-blue-600' : ''
                      }`}
                    >
                      {team}
                    </TeamLink>
                  );
                })}
              </div>
            </div>
          </div>
          <span className={`text-sm ${result.blueWon ? 'font-bold' : ''}`}>{result.blueScore}</span>
        </div>
      </div>
    );
  };

  // Special finals renderer showing individual match scores in columns
  const renderFinalsSection = () => {
    const finalsMatches = matches.filter(m => m.comp_level === 'f').sort((a, b) => a.match_number - b.match_number);
    if (finalsMatches.length === 0) return null;

    // Get the two competing alliances from the first finals match
    const firstMatch = finalsMatches[0];
    const matchRedTeams = firstMatch.alliances.red.team_keys.map(t => t.substring(3));
    const matchBlueTeams = firstMatch.alliances.blue.team_keys.map(t => t.substring(3));
    
    // Get alliance numbers and full alliance rosters
    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);
    
    // Get full alliance rosters (all teams, not just the 3 that played)
    const redTeams = redAllianceNumber ? alliances[redAllianceNumber - 1].picks.map(pick => pick.substring(3)) : matchRedTeams;
    const blueTeams = blueAllianceNumber ? alliances[blueAllianceNumber - 1].picks.map(pick => pick.substring(3)) : matchBlueTeams;

    // Calculate total wins for each alliance
    let redWins = 0;
    let blueWins = 0;

    finalsMatches.forEach(match => {
      if (match.alliances.red.score !== -1 && match.alliances.blue.score !== -1) {
        if (match.alliances.red.score > match.alliances.blue.score) {
          redWins++;
        } else if (match.alliances.blue.score > match.alliances.red.score) {
          blueWins++;
        }
      }
    });

    const redWonSeries = redWins > blueWins;
    const blueWonSeries = blueWins > redWins;

    return (
      <div className="border border-gray-300 rounded bg-white mb-2 w-72">
        <div className="bg-gray-100 px-2 py-1 text-sm font-bold border-b flex justify-between items-center">
          <span>Finals</span>
          <div className="flex gap-1 items-center mr-1">
            {finalsMatches.map((match, idx) => {
              const videoURL = maybeGetFirstMatchVideoURL(match);
              return videoURL ? (
                <Link key={idx} to={videoURL} className="text-gray-600 hover:text-gray-800 flex items-center justify-center" style={{minWidth: '20px'}}>
                  <PlayCircle className="inline w-4 h-4" />
                </Link>
              ) : (
                <div key={idx} className="w-4 h-4 flex items-center justify-center" style={{minWidth: '20px'}}></div>
              );
            })}
          </div>
        </div>
        <div className="px-2 py-1 flex justify-between items-center bg-red-100">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-3">
              {redAllianceNumber && (
                <span className="text-sm font-semibold text-red-800">
                  #{redAllianceNumber}
                </span>
              )}
              <div className="flex gap-1">
                {redTeams.map((team, idx) => {
                  const teamPlayed = matchRedTeams.includes(team);
                  const showUnderlines = redTeams.length > 3; // Only show underlines if there are backup teams
                  return (
                    <TeamLink
                      key={team}
                      teamOrKey={`frc${team}`}
                      year={year}
                      className={`text-sm ${redWonSeries ? 'font-bold' : ''} w-10 text-left text-red-600 ${
                        showUnderlines && teamPlayed ? 'underline decoration-dotted decoration-red-600' : ''
                      }`}
                    >
                      {team}
                    </TeamLink>
                  );
                })}
              </div>
            </div>
          </div>
          <div className="flex gap-1 min-w-0">
            {finalsMatches.map((match, idx) => (
              <span key={idx} className={`text-sm ${match.alliances.red.score > match.alliances.blue.score ? 'font-bold' : ''} flex-shrink-0`}>
                {match.alliances.red.score !== -1 ? match.alliances.red.score : '-'}
              </span>
            ))}
          </div>
        </div>
        <div className="px-2 py-1 flex justify-between items-center bg-blue-100">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-3">
              {blueAllianceNumber && (
                <span className="text-sm font-semibold text-blue-800">
                  #{blueAllianceNumber}
                </span>
              )}
              <div className="flex gap-1">
                {blueTeams.map((team, idx) => {
                  const teamPlayed = matchBlueTeams.includes(team);
                  const showUnderlines = blueTeams.length > 3; // Only show underlines if there are backup teams
                  return (
                    <TeamLink
                      key={team}
                      teamOrKey={`frc${team}`}
                      year={year}
                      className={`text-sm ${blueWonSeries ? 'font-bold' : ''} w-10 text-left text-blue-600 ${
                        showUnderlines && teamPlayed ? 'underline decoration-dotted decoration-blue-600' : ''
                      }`}
                    >
                      {team}
                    </TeamLink>
                  );
                })}
              </div>
            </div>
          </div>
          <div className="flex gap-1 min-w-0">
            {finalsMatches.map((match, idx) => (
              <span key={idx} className={`text-sm ${match.alliances.blue.score > match.alliances.red.score ? 'font-bold' : ''} flex-shrink-0`}>
                {match.alliances.blue.score !== -1 ? match.alliances.blue.score : '-'}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-bold mb-4">Playoff Bracket</h2>
      
      <div className="overflow-x-auto overflow-y-hidden">
        <div className="flex gap-8 justify-start items-start min-w-max px-4">
        
        {/* Left Side: Upper and Lower Brackets */}
        <div className="space-y-4">
          
          {/* Upper Bracket */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-center">Upper Bracket</h2>
            <div className="flex gap-6 items-start">
              
              {/* Round 1 */}
              <div className="flex flex-col items-center">
                <h3 className="font-bold mb-4 text-center">Round 1</h3>
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
                <h3 className="font-bold mb-4 text-center">Round 2</h3>
                <div className="space-y-4">
                  <div className="h-4"></div>
                  {renderMatch(7, 'Match 7')}
                  <div className="h-28"></div>
                  {renderMatch(8, 'Match 8')}
                </div>
              </div>

              {/* Round 4 */}
              <div className="flex flex-col items-center">
                <h3 className="font-bold mb-4 text-center">Round 4</h3>
                <div className="space-y-4">
                  <div className="h-32"></div>
                  {renderMatch(11, 'Match 11')}
                </div>
              </div>
              
            </div>
          </div>
          
          {/* Lower Bracket */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-center">Lower Bracket</h2>
            <div className="flex gap-6 items-start">
              
              {/* Round 1 */}
              <div className="flex flex-col items-center">
                <h3 className="font-bold mb-4 text-center">Round 1</h3>
                <div className="space-y-4">
                  {renderMatch(5, 'Match 5')}
                  <div className="h-6"></div>
                  {renderMatch(6, 'Match 6')}
                </div>
              </div>

              {/* Round 2 */}
              <div className="flex flex-col items-center">
                <h3 className="font-bold mb-4 text-center">Round 2</h3>
                <div className="space-y-4">
                  {renderMatch(10, 'Match 10')}
                  <div className="h-6"></div>
                  {renderMatch(9, 'Match 9')}
                </div>
              </div>

              {/* Round 4 */}
              <div className="flex flex-col items-center">
                <h3 className="font-bold mb-4 text-center">Round 4</h3>
                <div className="space-y-4">
                  <div className="h-8"></div>
                  {renderMatch(12, 'Match 12')}
                </div>
              </div>

              {/* Round 5 */}
              <div className="flex flex-col items-center">
                <h3 className="font-bold mb-4 text-center">Round 5</h3>
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
          <h3 className="font-bold mb-4 text-center">Finals</h3>
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