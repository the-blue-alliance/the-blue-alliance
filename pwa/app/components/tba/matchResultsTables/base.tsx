import { Tooltip } from '@radix-ui/react-tooltip';
import { Link } from '@remix-run/react';
import { type VariantProps, cva } from 'class-variance-authority';
import type React from 'react';
import { Fragment } from 'react';
import { Match } from '~/api/v3';
import {
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { cn, timestampsAreOnDifferentDays, zip } from '~/lib/utils';
import PlayCircle from '~icons/bi/play-circle';

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

interface CellProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cellVariants> {
  dq?: boolean;
  surrogate?: boolean;
}
function GridCell({
  className,
  matchResult,
  allianceColor,
  teamOrScore,
  dq,
  surrogate,
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
        },
      )}
      {...props}
    />
  );
}

function maybeGetFirstMatchVideoURL(match: Match): string | undefined {
  if (match.videos === undefined || match.videos.length === 0) {
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

export default function MatchResultsTableBase({
  matches,
  matchTitleFormatter,
}: {
  matches: Match[];
  matchTitleFormatter: (match: Match) => string;
}) {
  const gridStyle = cn(
    // always use these classes:
    'grid items-center justify-items-center',
    '[&>*]:justify-self-stretch [&>*]:justify-center',
    '[&>*]:text-center [&>*]:p-[5px] [&>*]:h-full [&>*]:content-center',
    // use these classes on mobile:
    'grid-rows-2',
    'grid-cols-[calc(1.25em+10px)_8em_1fr_1fr_1fr_1fr]', // 6 columns of these sizes
    'border-[#000] border-b-[1px]',
    '[&>*]:border-[#ddd] [&>*]:border-[1px]',
    // use these on desktop:
    'lg:grid-rows-1',
    'lg:grid-cols-[calc(1.25em+6px*2)_8em_repeat(6,minmax(0,1fr))_0.9fr_0.9fr]',
    'lg:border-[#ddd] lg:border-b-[1px]',
    '[&>*]:lg:border-0 [&>*]:lg:border-r-[1px]', // reset the border, then apply one to the right
  );

  return (
    <div className="border-l border-t border-[#ddd]">
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
            matches[i - 1].actual_time &&
            m.actual_time &&
            // TODO: add timezone support
            timestampsAreOnDifferentDays(
              matches[i - 1].actual_time ?? m.actual_time,
              m.actual_time,
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
              {m.videos !== undefined && m.videos.length > 0 && (
                <Link to={maybeGetFirstMatchVideoURL(m) ?? '#'}>
                  <PlayCircle className="inline" />
                </Link>
              )}
            </GridCell>
            <GridCell className="row-span-2">{matchTitleFormatter(m)}</GridCell>

            {/* red alliance */}
            {m.alliances?.red?.team_keys.map((k) => {
              const dq = m.alliances?.red?.dq_team_keys?.includes(k);
              const surrogate =
                m.alliances?.red?.surrogate_team_keys?.includes(k);
              return (
                <GridCell
                  key={k}
                  allianceColor={'red'}
                  matchResult={
                    m.winning_alliance === 'red' ? 'winner' : 'loser'
                  }
                  dq={dq}
                  surrogate={surrogate}
                >
                  <ConditionalTooltip dq={dq} surrogate={surrogate}>
                    <Link to={`/team/${k?.substring(3)}`}>
                      {k?.substring(3)}
                    </Link>
                  </ConditionalTooltip>
                </GridCell>
              );
            })}

            {/* blue alliance */}
            {zip(m.alliances?.blue?.team_keys, [
              'col-start-3 row-start-2 lg:col-start-6 lg:row-start-1',
              'col-start-4 row-start-2 lg:col-start-7 lg:row-start-1',
              'col-start-5 row-start-2 lg:col-start-8 lg:row-start-1',
            ]).map(([k, x]) => {
              const dq = m.alliances?.blue?.dq_team_keys?.includes(k);
              const surrogate =
                m.alliances?.blue?.surrogate_team_keys?.includes(k);
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
                >
                  <ConditionalTooltip dq={dq} surrogate={surrogate}>
                    <Link to={`/team/${k?.substring(3)}`}>
                      {k?.substring(3)}
                    </Link>
                  </ConditionalTooltip>
                </GridCell>
              );
            })}

            {/* scores */}
            <GridCell
              className="col-start-6 row-start-1 lg:col-start-9"
              allianceColor={'red'}
              matchResult={m.winning_alliance === 'red' ? 'winner' : 'loser'}
              teamOrScore={'score'}
            >
              {m.alliances?.red?.score}
            </GridCell>
            <GridCell
              className="col-start-6 lg:col-start-10"
              allianceColor={'blue'}
              matchResult={m.winning_alliance === 'blue' ? 'winner' : 'loser'}
              teamOrScore={'score'}
            >
              {m.alliances?.blue?.score}
            </GridCell>
          </div>
        </Fragment>
      ))}
    </div>
  );
}
