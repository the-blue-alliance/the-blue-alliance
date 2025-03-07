import { Tooltip } from '@radix-ui/react-tooltip';
import { type VariantProps, cva } from 'class-variance-authority';
import { groupBy } from 'lodash-es';
import type React from 'react';
import { Fragment, useMemo } from 'react';
import { Link } from 'react-router';

import PlayCircle from '~icons/bi/play-circle';

import { Event, Match, Team } from '~/api/v3';
import { TeamLink } from '~/components/tba/links';
import RpDots from '~/components/tba/rpDot';
import {
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { DOUBLE_ELIM_ROUND_MAPPING, PlayoffType } from '~/lib/api/PlayoffType';
import { matchTitleShort, sortMatchComparator } from '~/lib/matchUtils';
import { cn, timestampsAreOnDifferentDays, zip } from '~/lib/utils';

const cellVariants = cva('', {
  variants: {
    matchResult: {
      winner: 'font-semibold',
      loser: '',
    },
    allianceColor: {
      red: 'bg-alliance-red-light',
      blue: 'bg-alliance-blue-light',
    },
    teamOrScore: {
      team: '',
      score: '',
    },
  },
  defaultVariants: {
    matchResult: 'loser',
    allianceColor: undefined,
    teamOrScore: 'team',
  },
  compoundVariants: [
    {
      allianceColor: 'red',
      teamOrScore: 'score',
      class: 'bg-alliance-red-dark',
    },
    {
      allianceColor: 'blue',
      teamOrScore: 'score',
      class: 'bg-alliance-blue-dark',
    },
  ],
});

// todo: implement RP dot markers
interface CellProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cellVariants> {
  dq?: boolean;
  surrogate?: boolean;
  teamHighlight?: boolean;
}
function GridCell({
  className,
  matchResult,
  allianceColor,
  teamOrScore,
  dq,
  surrogate,
  teamHighlight,
  ...props
}: CellProps) {
  return (
    <div
      className={cn(
        cellVariants({ matchResult, allianceColor, teamOrScore }),
        className,
        {
          'line-through': dq,
          'underline decoration-dotted': surrogate,
          underline: teamHighlight,
        },
      )}
      {...props}
    />
  );
}

function maybeGetFirstMatchVideoURL(match: Match): string | undefined {
  if (match.videos.length === 0) {
    return undefined;
  }

  return `https://www.youtube.com/watch?v=${match.videos[0].key}`;
}

function ConditionalTooltip({
  children,
  dq,
  surrogate,
}: {
  children: React.ReactNode;
  dq: boolean;
  surrogate: boolean;
}) {
  if (dq || surrogate) {
    return (
      <TooltipProvider delayDuration={100}>
        <Tooltip>
          <TooltipTrigger asChild>{children}</TooltipTrigger>
          <TooltipContent className="font-normal">
            {dq && 'DQ'}
            {dq && surrogate && ' | '}
            {surrogate && 'Surrogate'}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }
  return <>{children}</>;
}

interface MatchResultsTableProps {
  matches: Match[];
  team?: Team;
  event: Event;
}

export default function MatchResultsTable(props: MatchResultsTableProps) {
  props.matches.sort(sortMatchComparator);

  const hasPlayoffs =
    props.matches.filter((m) => m.comp_level !== 'qm').length > 0;

  const groupByRound =
    hasPlayoffs &&
    (props.event.playoff_type == PlayoffType.DOUBLE_ELIM_4_TEAM ||
      props.event.playoff_type == PlayoffType.DOUBLE_ELIM_8_TEAM);

  const dividersBetweenRounds = !groupByRound && hasPlayoffs;

  const matchesGroupedByRound = useMemo(
    () =>
      groupByRound
        ? groupBy(
            props.matches.filter(
              (m) => m.comp_level !== 'f' && m.comp_level !== 'qm',
            ),
            (m) => DOUBLE_ELIM_ROUND_MAPPING.get(m.set_number) ?? 1,
          )
        : {},
    [groupByRound, props.matches],
  );

  const finals = useMemo(
    () => props.matches.filter((m) => m.comp_level === 'f'),
    [props.matches],
  );

  const quals = useMemo(
    () => props.matches.filter((m) => m.comp_level === 'qm'),
    [props.matches],
  );

  // TODO: implement me for 2022 and prior single elim bracket tables
  // (the grey divider boxes between rows)
  if (dividersBetweenRounds) {
    return <MatchResultsTableGroup {...props} />;
  }

  if (!hasPlayoffs) {
    return <MatchResultsTableGroup {...props} />;
  }

  return (
    <>
      {quals.length > 0 && (
        <>
          <div className="mt-1.5 text-lg">Quals</div>
          <MatchResultsTableGroup {...props} matches={quals} />
        </>
      )}
      {Object.entries(matchesGroupedByRound).map(([round, matches]) => (
        <div key={round}>
          <div className="mt-1.5 text-lg">Round {round}</div>
          <MatchResultsTableGroup {...props} matches={matches} />
        </div>
      ))}

      {finals.length > 0 && (
        <>
          <div className="mt-1.5 text-lg">Finals</div>
          <MatchResultsTableGroup {...props} matches={finals} />
        </>
      )}
    </>
  );
}

// todo: add support for specific-team underlines
function MatchResultsTableGroup({
  matches,
  event,
  team,
}: MatchResultsTableProps) {
  const gridStyle = cn(
    // always use these classes:
    'grid items-center justify-items-center',
    '*:justify-self-stretch *:justify-center',
    '*:text-center *:p-[5px] *:h-full *:content-center',
    // use these classes on mobile:
    'grid-rows-2',
    'grid-cols-[calc(1.25em+10px)_8em_1fr_1fr_1fr_1fr]', // 6 columns of these sizes
    'border-[#000] border-b-[1px]',
    '*:border-[#ddd] *:border-[1px]',
    // use these on desktop:
    'lg:grid-rows-1',
    'lg:grid-cols-[calc(1.25em+6px*2)_10em_repeat(6,minmax(0,1fr))_0.9fr_0.9fr]',
    'lg:border-[#ddd] lg:border-b-[1px]',
    'lg:*:border-0 lg:*:border-r-[1px]', // reset the border, then apply one to the right
  );

  return (
    <div className="min-w-[25rem] border-l border-t border-[#ddd] md:min-w-[35rem]">
      <div className={cn(gridStyle, 'bg-[#f0f0f0] font-semibold')}>
        <div className="row-span-2 lg:row-span-1">
          <PlayCircle className="inline" />
        </div>
        <div className="row-span-2 lg:row-span-1">Match</div>
        <div className="col-span-3 lg:col-span-3">Red Alliance</div>
        <div className="col-span-3 col-start-3 lg:col-start-6">
          Blue Alliance
        </div>
        <div className="col-start-6 row-span-2 row-start-1 lg:col-span-2 lg:col-start-9">
          Scores
        </div>
      </div>

      {matches.map((m, i) => (
        <Fragment key={m.key}>
          {i > 0 &&
            matches[i - 1].time &&
            m.time &&
            timestampsAreOnDifferentDays(
              matches[i - 1].time ?? m.time,
              m.time,
              event.timezone,
            ) && (
              <div
                className={cn(
                  'bg-[#f0f0f0]',
                  'font-semibold',
                  'grid-cols-1',
                  'align-middle',
                  'text-center',
                  'grid-rows-1',
                  'py-1',
                  'border-b-[1px]',
                  'border-[#000]',
                  'lg:border-[#ddd]',
                )}
              >
                <GridCell>End of Day</GridCell>
              </div>
            )}

          <div className={gridStyle}>
            {/* play button and match title */}
            <GridCell className="row-span-2">
              {m.videos.length > 0 && (
                <Link to={maybeGetFirstMatchVideoURL(m) ?? '#'}>
                  <PlayCircle className="inline" />
                </Link>
              )}
            </GridCell>
            <GridCell className="row-span-2">
              {matchTitleShort(m, event)}
            </GridCell>

            {/* red alliance */}
            {m.alliances.red.team_keys.map((k) => {
              const dq = m.alliances.red.dq_team_keys.includes(k);
              const surrogate = m.alliances.red.surrogate_team_keys.includes(k);
              return (
                <GridCell
                  key={k}
                  allianceColor={'red'}
                  matchResult={
                    m.winning_alliance === 'red' ? 'winner' : 'loser'
                  }
                  dq={dq}
                  surrogate={surrogate}
                  teamHighlight={team?.key === k}
                >
                  <ConditionalTooltip dq={dq} surrogate={surrogate}>
                    <TeamLink teamOrKey={k} year={event.year}>
                      {k.substring(3)}
                    </TeamLink>
                  </ConditionalTooltip>
                </GridCell>
              );
            })}

            {/* blue alliance */}
            {zip(m.alliances.blue.team_keys, [
              'col-start-3 row-start-2 lg:col-start-6 lg:row-start-1',
              'col-start-4 row-start-2 lg:col-start-7 lg:row-start-1',
              'col-start-5 row-start-2 lg:col-start-8 lg:row-start-1',
            ]).map(([k, x]) => {
              const dq = m.alliances.blue.dq_team_keys.includes(k);
              const surrogate =
                m.alliances.blue.surrogate_team_keys.includes(k);
              return (
                <GridCell
                  key={k}
                  allianceColor={'blue'}
                  matchResult={
                    m.winning_alliance === 'blue' ? 'winner' : 'loser'
                  }
                  className={x}
                  dq={dq}
                  surrogate={surrogate}
                  teamHighlight={team?.key === k}
                >
                  <ConditionalTooltip dq={dq} surrogate={surrogate}>
                    <TeamLink teamOrKey={k} year={event.year}>
                      {k.substring(3)}
                    </TeamLink>
                  </ConditionalTooltip>
                </GridCell>
              );
            })}

            {/* unplayed match */}
            {m.alliances.red.score == -1 && m.alliances.blue.score == -1 && (
              <GridCell
                className="relative col-start-6 row-span-2 row-start-1 lg:col-span-2 lg:col-start-9 lg:row-span-1"
                teamOrScore={'score'}
              >
                {m.predicted_time && (
                  <div className="text-sm italic lg:text-xs">
                    {new Date(m.predicted_time * 1000).toLocaleTimeString(
                      'en-US',
                      {
                        hour: '2-digit',
                        minute: '2-digit',
                        weekday: 'short',
                        hour12: true,
                      },
                    )}
                  </div>
                )}
              </GridCell>
            )}

            {m.alliances.red.score !== -1 && m.alliances.blue.score !== -1 && (
              <>
                {/* scores */}
                <GridCell
                  className="relative col-start-6 row-start-1 lg:col-start-9"
                  allianceColor={'red'}
                  matchResult={
                    m.winning_alliance === 'red' ? 'winner' : 'loser'
                  }
                  teamOrScore={'score'}
                  teamHighlight={
                    team !== undefined &&
                    m.alliances.red.team_keys.includes(team.key)
                  }
                >
                  {m.score_breakdown && (
                    <RpDots
                      score_breakdown={m.score_breakdown.red}
                      year={Number(m.key.substring(0, 4))}
                    />
                  )}
                  {m.alliances.red.score}
                </GridCell>
                <GridCell
                  className="relative col-start-6 lg:col-start-10"
                  allianceColor={'blue'}
                  matchResult={
                    m.winning_alliance === 'blue' ? 'winner' : 'loser'
                  }
                  teamOrScore={'score'}
                  teamHighlight={
                    team !== undefined &&
                    m.alliances.blue.team_keys.includes(team.key)
                  }
                >
                  {m.score_breakdown && (
                    <RpDots
                      score_breakdown={m.score_breakdown.blue}
                      year={Number(m.key.substring(0, 4))}
                    />
                  )}
                  {m.alliances.blue.score}
                </GridCell>
              </>
            )}
          </div>
        </Fragment>
      ))}
    </div>
  );
}
