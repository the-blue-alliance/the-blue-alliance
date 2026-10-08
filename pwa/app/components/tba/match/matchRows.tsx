import { Link } from '@tanstack/react-router';
import { cn } from 'cn';

import BiStarFill from '~icons/bi/star-fill';
import HourglassIcon from '~icons/ic/baseline-hourglass-empty';
import PlayArrowIcon from '~icons/ic/baseline-play-arrow';
import PendingIcon from '~icons/ic/outline-pending';
import ChevronDownIcon from '~icons/lucide/chevron-down';
import PlayCircleIcon from '~icons/mdi/play-circle-outline';
import YoutubeIcon from '~icons/mdi/youtube';

import { AllianceColor, Event, Match, PlayoffType } from '~/api/tba/read';
import { MatchLink } from '~/components/tba/links';
import { ShouldInsertBreakCallback } from '~/components/tba/match/breakers';
import ScoreCell from '~/components/tba/match/scoreCell';
import TeamListSubgrid from '~/components/tba/match/teamListSubgrid';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { useFavoriteTeamKeys } from '~/lib/hooks/useFavoriteTeams';
import { formatMatchTime, matchTitleShort } from '~/lib/matchUtils';
import type { NexusMatchStatus } from '~/lib/nexus';

interface PlaylistEntry {
  url: string;
  label: string;
}

// 50 is an artificial limit imposed by YouTube; not in our control
function buildYoutubePlaylistUrls(
  matches: Match[],
  title: string,
  chunkSize: number = 50,
): PlaylistEntry[] {
  const videoIds = matches
    .flatMap((m) => m.videos)
    .filter((v) => v.type === 'youtube')
    .map((v) => v.key.split('?')[0]);

  if (videoIds.length === 0) return [];

  const entries: PlaylistEntry[] = [];
  for (let i = 0; i < videoIds.length; i += chunkSize) {
    const chunk = videoIds.slice(i, i + chunkSize);
    const url = `https://www.youtube.com/watch_videos?video_ids=${chunk.join(',')}&title=${encodeURIComponent(title)}`;
    const label =
      videoIds.length <= chunkSize
        ? 'Watch All Videos'
        : `Videos ${i + 1}–${Math.min(i + chunkSize, videoIds.length)}`;
    entries.push({ url, label });
  }
  return entries;
}

export default function SimpleMatchRowsWithBreaks({
  matches,
  event,
  breakers,
  focusTeamKey,
  nexusStatusByKey,
}: {
  matches: Match[];
  event: Event;
  breakers: ShouldInsertBreakCallback[];
  focusTeamKey?: string;
  nexusStatusByKey?: Record<string, NexusMatchStatus>;
}) {
  const playlistUrls = buildYoutubePlaylistUrls(matches, event.name);
  let firstBreakRowSeen = false;
  let zebraIdx = 0;
  const divs = [];

  for (let i = 0; i < matches.length; i++) {
    const match = matches[i];
    const maybeNextMatch = i < matches.length - 1 ? matches[i + 1] : null;

    for (let bi = 0; bi < breakers.length; bi++) {
      const result = breakers[bi]({
        match,
        matchIndex: i,
        nextMatch: maybeNextMatch,
        event,
      });

      if (result.shouldBreak && result.whereToInsertBreak === 'before') {
        const isFirst = !firstBreakRowSeen;
        firstBreakRowSeen = true;
        divs.push(
          <BreakRow
            key={`break-before-${i}-${bi}`}
            text={result.text ?? 'Break'}
            size={result.size}
            playlists={isFirst ? playlistUrls : undefined}
          />,
        );
      }
    }

    divs.push(
      <MatchRow
        match={match}
        event={event}
        year={event.year}
        key={match.key}
        focusTeamKey={focusTeamKey}
        nexusStatus={nexusStatusByKey?.[match.key]}
        className={cn(
          zebraIdx % 2 === 0 && 'bg-neutral-50 dark:bg-neutral-900',
        )}
      />,
    );
    zebraIdx++;

    for (let bi = 0; bi < breakers.length; bi++) {
      const result = breakers[bi]({
        match,
        matchIndex: i,
        nextMatch: maybeNextMatch,
        event,
      });

      if (result.shouldBreak && result.whereToInsertBreak === 'after') {
        const isFirst = !firstBreakRowSeen;
        firstBreakRowSeen = true;
        divs.push(
          <BreakRow
            key={`break-after-${i}-${bi}`}
            text={result.text ?? 'Break'}
            size={result.size}
            playlists={isFirst ? playlistUrls : undefined}
          />,
        );
      }
    }
  }

  return <div className="@container flex flex-col divide-y">{divs}</div>;
}

const NEXUS_STATUS_ICONS: Record<NexusMatchStatus, React.ReactNode> = {
  'On field': <PlayArrowIcon className="size-5 text-green-600" />,
  'On deck': <PendingIcon className="size-5 text-blue-500" />,
  'Now queuing': <HourglassIcon className="size-5 text-orange-500" />,
};

function NexusStatusIconWithTooltip({ status }: { status: NexusMatchStatus }) {
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            className="mx-2 inline-flex items-center justify-center"
            aria-label={`Nexus status: ${status}`}
          />
        }
      >
        {NEXUS_STATUS_ICONS[status]}
      </TooltipTrigger>
      <TooltipContent sideOffset={6}>{status}</TooltipContent>
    </Tooltip>
  );
}

export function MatchRow({
  match,
  event,
  year,
  focusTeamKey,
  nexusStatus,
  className,
}: {
  match: Match;
  event: Event;
  year: number;
  focusTeamKey?: string;
  nexusStatus?: NexusMatchStatus;
  className?: string;
}) {
  const playoffType = event.playoff_type ?? PlayoffType.CUSTOM;
  const maybeVideoURL = maybeGetFirstMatchVideoURL(match);
  const isPlayed =
    match.alliances.red.score !== -1 && match.alliances.blue.score !== -1;
  const matchTime = match.predicted_time ?? match.time;
  const focusedAlliance = focusTeamKey
    ? match.alliances.red.team_keys.includes(focusTeamKey)
      ? AllianceColor.RED
      : match.alliances.blue.team_keys.includes(focusTeamKey)
        ? AllianceColor.BLUE
        : null
    : null;
  const { teamKeys: favoriteTeamKeys } = useFavoriteTeamKeys();
  const hasFavorite = [
    ...match.alliances.red.team_keys,
    ...match.alliances.blue.team_keys,
  ].some((teamKey) => favoriteTeamKeys.includes(teamKey));

  /* Desktop: 1x11 grid, Mobile: 2x6 grid */
  return (
    <div
      className={cn(
        `mx-auto grid w-full max-w-6xl grid-cols-[2.5em_7em_repeat(4,1fr)]
        grid-rows-[2em_2em] gap-0.5 text-sm numeric-data
        @min-[34rem]:grid-cols-[2.5em_7em_repeat(9,1fr)]
        @min-[34rem]:grid-rows-1`,
        className,
      )}
    >
      {/* Play Button */}
      <div
        className="row-span-2 flex items-center justify-center rounded-tl-lg
          @min-[34rem]:col-span-1 @min-[34rem]:row-span-1
          @min-[34rem]:rounded-l-lg"
      >
        {maybeVideoURL ? (
          <Link
            to={maybeVideoURL}
            target="_blank"
            rel="noopener noreferrer"
            className="mx-2"
          >
            <PlayCircleIcon />
          </Link>
        ) : nexusStatus ? (
          <NexusStatusIconWithTooltip status={nexusStatus} />
        ) : null}
      </div>

      {/* Match Name */}
      <div
        className="row-span-2 flex items-center justify-center p-1.5
          @min-[34rem]:col-span-2 @min-[34rem]:row-span-1"
      >
        <span className="relative">
          {hasFavorite && (
            <span className="absolute top-1/2 right-full mr-1 -translate-y-1/2">
              <BiStarFill aria-hidden className="size-3 text-yellow-500" />
              <span className="sr-only">Includes a favorite team</span>
            </span>
          )}
          <MatchLink
            matchOrKey={match}
            event={event}
            className="text-center text-sm text-foreground"
          >
            {matchTitleShort(match, playoffType)}
          </MatchLink>
        </span>
      </div>

      {/* Red Team Players - Subgrid Component */}
      <TeamListSubgrid
        teamKeys={match.alliances.red.team_keys}
        allianceColor="red"
        className="col-span-3 pt-0.5 @min-[34rem]:col-span-3
          @min-[34rem]:pb-0.5"
        teamCellClassName="@max-[34rem]:first:rounded-tl-lg @max-[34rem]:last:rounded-tr-lg @min-[34rem]:first:rounded-l-lg"
        winner={match.winning_alliance === AllianceColor.RED}
        dq={match.alliances.red.dq_team_keys}
        surrogate={match.alliances.red.surrogate_team_keys}
        year={year}
        focusTeamKey={focusTeamKey}
        favoriteTeamKeys={favoriteTeamKeys}
      />

      {/* Blue Team Players - Subgrid Component */}
      <TeamListSubgrid
        teamKeys={match.alliances.blue.team_keys}
        allianceColor="blue"
        className="col-span-3 pb-0.5 @min-[34rem]:col-span-3
          @min-[34rem]:pt-0.5"
        teamCellClassName="@max-[34rem]:first:rounded-bl-lg @max-[34rem]:last:rounded-br-lg @min-[34rem]:last:rounded-r-lg"
        winner={match.winning_alliance === AllianceColor.BLUE}
        dq={match.alliances.blue.dq_team_keys}
        surrogate={match.alliances.blue.surrogate_team_keys}
        year={year}
        focusTeamKey={focusTeamKey}
        favoriteTeamKeys={favoriteTeamKeys}
      />

      {!isPlayed && (
        <div
          className="col-start-6 row-span-2 row-start-1 @min-[34rem]:col-span-2
            @min-[34rem]:col-start-auto @min-[34rem]:row-span-1
            @min-[34rem]:row-start-auto"
        >
          <span className="flex h-full items-center justify-center text-center">
            {matchTime && formatMatchTime(matchTime)}
          </span>
        </div>
      )}

      {/* Red Score */}
      {isPlayed && (
        <ScoreCell
          score={match.alliances.red.score}
          allianceColor="red"
          className="col-start-6 row-start-1 mt-0.5 @max-[34rem]:rounded-t-lg
            @min-[34rem]:col-span-1 @min-[34rem]:col-start-auto
            @min-[34rem]:row-start-auto @min-[34rem]:mb-0.5
            @min-[34rem]:rounded-l-lg"
          winner={match.winning_alliance === AllianceColor.RED}
          scoreBreakdown={match.score_breakdown?.red}
          year={year}
          compLevel={match.comp_level}
          focused={focusedAlliance === AllianceColor.RED}
        />
      )}

      {/* Blue Score */}
      {isPlayed && (
        <ScoreCell
          score={match.alliances.blue.score}
          allianceColor="blue"
          className="col-start-6 row-start-2 mb-0.5 @max-[34rem]:rounded-b-lg
            @min-[34rem]:col-span-1 @min-[34rem]:col-start-auto
            @min-[34rem]:row-start-auto @min-[34rem]:mt-0.5
            @min-[34rem]:rounded-r-lg"
          winner={match.winning_alliance === AllianceColor.BLUE}
          scoreBreakdown={match.score_breakdown?.blue}
          year={year}
          compLevel={match.comp_level}
          focused={focusedAlliance === AllianceColor.BLUE}
        />
      )}
    </div>
  );
}

// Used on match pages, omits the play button and match title
export function SimpleMatchRow({
  match,
  year,
}: {
  match: Match;
  year: number;
}) {
  const isPlayed =
    match.alliances.red.score !== -1 && match.alliances.blue.score !== -1;
  const matchTime = match.predicted_time ?? match.time;

  return (
    <div>
      {/* 3x4 grid with header row */}
      <div
        className="mx-auto grid w-full max-w-6xl grid-cols-[repeat(4,1fr)]
          grid-rows-[auto_repeat(2,2em)] gap-x-1 text-sm numeric-data"
      >
        {/* Header: Teams */}
        <div
          className="col-span-3 col-start-1 row-start-1 flex items-center
            justify-center text-sm font-semibold"
        >
          Teams
        </div>

        {/* Header: Score */}
        <div
          className="col-start-4 row-start-1 flex items-center justify-center
            text-sm font-semibold"
        >
          Score
        </div>

        {/* Red Team Players - Subgrid Component */}
        <TeamListSubgrid
          teamKeys={match.alliances.red.team_keys}
          allianceColor="red"
          className="col-span-3 col-start-1 row-start-2"
          teamCellClassName="first:rounded-tl-lg last:rounded-tr-lg"
          winner={match.winning_alliance === AllianceColor.RED}
          dq={match.alliances.red.dq_team_keys}
          surrogate={match.alliances.red.surrogate_team_keys}
          year={year}
        />

        {/* Blue Team Players - Subgrid Component */}
        <TeamListSubgrid
          teamKeys={match.alliances.blue.team_keys}
          allianceColor="blue"
          className="col-span-3 col-start-1 row-start-3"
          teamCellClassName="first:rounded-bl-lg last:rounded-br-lg"
          winner={match.winning_alliance === AllianceColor.BLUE}
          dq={match.alliances.blue.dq_team_keys}
          surrogate={match.alliances.blue.surrogate_team_keys}
          year={year}
        />

        {!isPlayed && (
          <div
            className="col-start-4 row-span-2 row-start-2 flex items-center
              justify-center text-center"
          >
            <span>{matchTime && formatMatchTime(matchTime)}</span>
          </div>
        )}

        {/* Red Score */}
        {isPlayed && (
          <ScoreCell
            score={match.alliances.red.score}
            allianceColor="red"
            className="col-start-4 row-start-2 rounded-tl-lg rounded-tr-lg"
            winner={match.winning_alliance === AllianceColor.RED}
            scoreBreakdown={match.score_breakdown?.red}
            year={year}
            compLevel={match.comp_level}
          />
        )}

        {/* Blue Score */}
        {isPlayed && (
          <ScoreCell
            score={match.alliances.blue.score}
            allianceColor="blue"
            className="col-start-4 row-start-3 rounded-br-lg rounded-bl-lg"
            winner={match.winning_alliance === AllianceColor.BLUE}
            scoreBreakdown={match.score_breakdown?.blue}
            year={year}
            compLevel={match.comp_level}
          />
        )}
      </div>
    </div>
  );
}

function maybeGetFirstMatchVideoURL(match: Match): string | undefined {
  if (match.videos.length === 0) {
    return undefined;
  }

  // Video key may contain start time query param (e.g., "?t=123"); convert "?" to "&" for watch?v= URL structure
  return `https://www.youtube.com/watch?v=${match.videos[0].key.replace('?', '&')}`;
}

interface BreakRowProps extends React.HTMLAttributes<HTMLDivElement> {
  text: string;
  size?: 'default' | 'small';
  playlists?: PlaylistEntry[];
}
export function BreakRow({
  className,
  text,
  size = 'default',
  playlists,
  ...props
}: BreakRowProps) {
  return (
    <div
      className={cn('col-span-11 flex rounded-md bg-muted', className)}
      {...props}
    >
      <div
        className={cn(
          `grid w-full grid-cols-[1fr_auto_1fr] items-center gap-2 px-2
          font-medium`,
          size === 'small' ? 'h-5 text-xs' : 'h-8 text-sm',
        )}
      >
        <span className="col-start-2">{text}</span>
        {playlists && playlists.length > 0 && (
          <div className="flex items-center justify-self-end whitespace-nowrap">
            {playlists.length === 1 ? (
              <a
                href={playlists[0].url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-muted-foreground
                  transition-colors hover:text-foreground"
              >
                <YoutubeIcon className="size-3.5" />
                {playlists[0].label}
              </a>
            ) : (
              <DropdownMenu>
                <DropdownMenuTrigger
                  className="flex cursor-pointer items-center gap-1
                    text-muted-foreground transition-colors
                    hover:text-foreground"
                >
                  <YoutubeIcon className="size-3.5" />
                  Watch Videos
                  <ChevronDownIcon className="size-3" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {playlists.map(({ url, label }) => (
                    <DropdownMenuItem
                      key={url}
                      render={
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex cursor-pointer items-center gap-2"
                        >
                          <YoutubeIcon className="size-3.5" />
                          {label}
                        </a>
                      }
                    />
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
