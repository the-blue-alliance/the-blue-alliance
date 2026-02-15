import { type JSX, useMemo, useState } from 'react'; // trigger CI

import PlayCircleIcon from '~icons/mdi/play-circle-outline';

import { EliminationAlliance, Event, Match } from '~/api/tba/read';
import { MatchLink, TeamLink } from '~/components/tba/links';
import { Card, CardHeader, CardTitle } from '~/components/ui/card';
import { EventType } from '~/lib/api/EventType';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { getDivisionShortform } from '~/lib/eventUtils';
import { sortMatchComparator } from '~/lib/matchUtils';
import { cn } from '~/lib/utils';

type SeriesResult = {
  redTeams: string[];
  blueTeams: string[];
  redAllianceNumber: number | null;
  blueAllianceNumber: number | null;
  redResults: { score: number; won: boolean }[];
  blueResults: { score: number; won: boolean }[];
  redWon: boolean;
  blueWon: boolean;
  matchRedTeams: string[];
  matchBlueTeams: string[];
};

function BracketMatchCard({
  label,
  matches,
  event,
  hoveredAlliance,
  setHoveredAlliance,
  getSeriesResult,
  getAllianceDisplayName,
}: {
  label: string;
  matches: Match[] | undefined;
  event: Event;
  hoveredAlliance: number | null;
  setHoveredAlliance: (alliance: number | null) => void;
  getSeriesResult: (matches: Match[] | undefined) => SeriesResult | null;
  getAllianceDisplayName: (allianceNumber: number) => string;
}): JSX.Element | null {
  const result = getSeriesResult(matches);
  if (!result) return null;

  const isRedHighlighted = hoveredAlliance === result.redAllianceNumber;
  const isBlueHighlighted = hoveredAlliance === result.blueAllianceNumber;
  const isHighlighted = isRedHighlighted || isBlueHighlighted;

  return (
    <div
      className={cn(
        `min-w-40 overflow-hidden rounded-md border border-neutral-200
        bg-background transition-all duration-200 dark:border-neutral-700`,
        {
          [`border-transparent shadow-lg ring-2 ring-alliance-red/75
          dark:border-transparent`]: isHighlighted && result.redWon,
          [`border-transparent shadow-lg ring-2 ring-alliance-blue/75
          dark:border-transparent`]: isHighlighted && result.blueWon,
        },
      )}
    >
      <div
        className="flex items-center justify-between border-b px-2 py-1 text-sm
          font-bold"
      >
        <div className="flex items-center gap-1">
          <span>{label}</span>
          {result.redAllianceNumber && result.blueAllianceNumber && (
            <span className="text-xs font-normal">
              (
              <span
                className={cn(
                  'text-alliance-red transition-all duration-200',
                  isRedHighlighted &&
                    `rounded bg-red-100 px-1 text-sm dark:bg-red-900
                    dark:text-white`,
                )}
              >
                {getAllianceDisplayName(result.redAllianceNumber)}
              </span>{' '}
              vs{' '}
              <span
                className={cn(
                  'text-alliance-blue transition-all duration-200',
                  isBlueHighlighted &&
                    `rounded bg-blue-100 px-1 text-sm dark:bg-blue-900
                    dark:text-white`,
                )}
              >
                {getAllianceDisplayName(result.blueAllianceNumber)}
              </span>
              )
            </span>
          )}
        </div>
        <div className="flex items-center gap-5">
          {matches?.map((match) => (
            <MatchLink
              key={match.key}
              matchOrKey={match}
              event={event}
              className="flex items-center justify-center"
            >
              <PlayCircleIcon className="inline size-4" />
            </MatchLink>
          ))}
        </div>
      </div>
      <div
        className={`group flex cursor-pointer items-center justify-between
          bg-alliance-red/15 px-1 py-1 transition-colors duration-200
          data-[highlight=true]:bg-alliance-red
          data-[highlight=true]:text-white`}
        data-highlight={isRedHighlighted}
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
              if (!teamPlayed) return null;
              return (
                <span
                  key={team}
                  className={cn(
                    `w-12 text-center text-sm text-alliance-red
                    group-data-[highlight=true]:text-white`,
                    result.redWon && 'font-bold',
                  )}
                >
                  <TeamLink
                    className="text-inherit"
                    teamOrKey={`frc${team}`}
                    year={event.year}
                  >
                    {team}
                  </TeamLink>
                </span>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex min-w-0 gap-1">
            {result.redResults.map((r, i) => (
              <span
                key={i}
                className={cn(
                  'w-8 shrink-0 text-center text-sm',
                  r.won && 'font-bold',
                )}
              >
                {r.score !== -1 ? r.score : '-'}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div
        className={`group flex cursor-pointer items-center justify-between
          bg-alliance-blue/15 px-1 py-1 transition-colors duration-200
          data-[highlight=true]:bg-alliance-blue
          data-[highlight=true]:text-white`}
        data-highlight={isBlueHighlighted}
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
              if (!teamPlayed) return null;
              return (
                <span
                  key={team}
                  className={cn(
                    `w-12 text-center text-sm text-alliance-blue
                    group-data-[highlight=true]:text-white`,
                    result.blueWon && 'font-bold',
                  )}
                >
                  <TeamLink
                    className="text-inherit"
                    teamOrKey={`frc${team}`}
                    year={event.year}
                  >
                    {team}
                  </TeamLink>
                </span>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <div className="flex min-w-0 gap-1">
            {result.blueResults.map((r, i) => (
              <span
                key={i}
                className={cn(
                  'w-8 flex-shrink-0 text-center text-sm',
                  r.won && 'font-bold',
                )}
              >
                {r.score !== -1 ? r.score : '-'}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TraditionalBracket({
  alliances,
  matches,
  event,
}: {
  alliances: EliminationAlliance[];
  matches: Match[];
  event: Event;
}): JSX.Element {
  const [hoveredAlliance, setHoveredAlliance] = useState<number | null>(null);

  const is4Team =
    event.playoff_type === PlayoffType.BRACKET_4_TEAM ||
    event.playoff_type === PlayoffType.BRACKET_2_TEAM;

  // Group matches by comp_level and set_number
  const matchGroups = useMemo(() => {
    const groups: Record<string, Match[]> = {};
    for (const match of matches) {
      if (match.comp_level === 'qm') continue;
      const key = `${match.comp_level}_${match.set_number}`;
      (groups[key] ??= []).push(match);
    }
    for (const setMatches of Object.values(groups)) {
      setMatches.sort(sortMatchComparator);
    }
    return groups;
  }, [matches]);

  const getAllianceNumber = (teamKeys: string[]): number | null => {
    for (let i = 0; i < alliances.length; i++) {
      const allianceTeamKeys = alliances[i].picks.map((pick) =>
        pick.substring(3),
      );
      if (teamKeys.every((team) => allianceTeamKeys.includes(team))) {
        return i + 1;
      }
    }
    return null;
  };

  const getAllianceDisplayName = (allianceNumber: number): string => {
    if (!allianceNumber || allianceNumber > alliances.length) return '';
    const alliance = alliances[allianceNumber - 1];
    if (event.event_type === EventType.CMP_FINALS && alliance.name) {
      return getDivisionShortform(alliance.name);
    }
    return `#${allianceNumber}`;
  };

  const getSeriesResult = (
    setMatches: Match[] | undefined,
  ): SeriesResult | null => {
    if (!setMatches || setMatches.length === 0) return null;

    const matchRedTeams = setMatches[0].alliances.red.team_keys.map((t) =>
      t.substring(3),
    );
    const matchBlueTeams = setMatches[0].alliances.blue.team_keys.map((t) =>
      t.substring(3),
    );

    const redAllianceNumber = getAllianceNumber(matchRedTeams);
    const blueAllianceNumber = getAllianceNumber(matchBlueTeams);

    const redTeams = redAllianceNumber
      ? alliances[redAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchRedTeams;
    const blueTeams = blueAllianceNumber
      ? alliances[blueAllianceNumber - 1].picks.map((pick) => pick.substring(3))
      : matchBlueTeams;

    const redResults = setMatches.map((match) => ({
      score: match.alliances.red.score,
      won: match.winning_alliance === 'red',
    }));
    const blueResults = setMatches.map((match) => ({
      score: match.alliances.blue.score,
      won: match.winning_alliance === 'blue',
    }));

    const lastMatch = setMatches[setMatches.length - 1];
    const redWon = lastMatch.winning_alliance === 'red';
    const blueWon = lastMatch.winning_alliance === 'blue';

    return {
      redTeams,
      blueTeams,
      redAllianceNumber,
      blueAllianceNumber,
      redResults,
      blueResults,
      redWon,
      blueWon,
      matchRedTeams,
      matchBlueTeams,
    };
  };

  if (alliances.length === 0 || matches.length === 0) {
    return <></>;
  }

  const hasEighthFinals = matches.some((m) => m.comp_level === 'ef');

  return (
    <Card className="mt-12 bg-neutral-50/50 p-2 dark:bg-neutral-900/50">
      <CardHeader>
        <CardTitle>Playoff Bracket</CardTitle>
      </CardHeader>

      <div className="overflow-x-auto overflow-y-hidden">
        <div className="flex min-w-max items-start gap-8 px-4 pb-4">
          {/* Eighth-Finals (16-team only) */}
          {hasEighthFinals && (
            <div className="flex flex-col items-center">
              <h3 className="mb-4 text-center">Eighths</h3>
              <div className="space-y-3">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((setNum) => (
                  <BracketMatchCard
                    key={`ef_${setNum}`}
                    label={`EF ${setNum}`}
                    matches={matchGroups[`ef_${setNum}`]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Quarterfinals (8-team and 16-team) */}
          {!is4Team && (
            <div className="flex flex-col items-center">
              <h3 className="mb-4 text-center">Quarters</h3>
              <div
                className="flex flex-col justify-around gap-3"
                style={hasEighthFinals ? { minHeight: '100%' } : {}}
              >
                {[1, 2, 3, 4].map((setNum) => (
                  <BracketMatchCard
                    key={`qf_${setNum}`}
                    label={`QF ${setNum}`}
                    matches={matchGroups[`qf_${setNum}`]}
                    event={event}
                    hoveredAlliance={hoveredAlliance}
                    setHoveredAlliance={setHoveredAlliance}
                    getSeriesResult={getSeriesResult}
                    getAllianceDisplayName={getAllianceDisplayName}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Semifinals */}
          <div className="flex flex-col items-center">
            <h3 className="mb-4 text-center">Semis</h3>
            <div
              className="flex flex-col justify-around gap-3"
              style={{ minHeight: is4Team ? undefined : '100%' }}
            >
              {[1, 2].map((setNum) => (
                <BracketMatchCard
                  key={`sf_${setNum}`}
                  label={`SF ${setNum}`}
                  matches={matchGroups[`sf_${setNum}`]}
                  event={event}
                  hoveredAlliance={hoveredAlliance}
                  setHoveredAlliance={setHoveredAlliance}
                  getSeriesResult={getSeriesResult}
                  getAllianceDisplayName={getAllianceDisplayName}
                />
              ))}
            </div>
          </div>

          {/* Finals */}
          <div className="flex flex-col items-center">
            <h3 className="mb-4 text-center font-bold">Finals</h3>
            <div
              className="flex flex-col justify-center"
              style={{ minHeight: '100%' }}
            >
              <BracketMatchCard
                label="Finals"
                matches={matchGroups['f_1']}
                event={event}
                hoveredAlliance={hoveredAlliance}
                setHoveredAlliance={setHoveredAlliance}
                getSeriesResult={getSeriesResult}
                getAllianceDisplayName={getAllianceDisplayName}
              />
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
