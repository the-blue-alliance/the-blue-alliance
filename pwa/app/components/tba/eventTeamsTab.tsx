import { useQueries, useQueryClient } from '@tanstack/react-query';
import { Suspense, lazy, useMemo, useState } from 'react';

import MapIcon from '~icons/lucide/map';
import SearchIcon from '~icons/lucide/search';
import XIcon from '~icons/lucide/x';

import type { EventColors } from '~/api/colors';
import { getEventColorsOptions } from '~/api/colors/@tanstack/react-query.gen';
import type {
  Event,
  Match,
  Media,
  NexusPitMap as NexusPitMapData,
  Team,
  TeamEventStatus,
} from '~/api/tba/read';
import {
  getEventNexusInfoOptions,
  getEventTeamsStatusesOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import {
  PitLocationLink,
  TeamLink,
  TeamLocationLink,
} from '~/components/tba/links';
import LoadingSkeleton from '~/components/tba/loadingSkeleton';
import {
  CHANGE_IN_COMP_LEVEL_BREAKER,
  END_OF_DAY_BREAKER,
  START_OF_QUALS_BREAKER,
} from '~/components/tba/match/breakers';
import SimpleMatchRowsWithBreaks from '~/components/tba/match/matchRows';
import TeamAvatar from '~/components/tba/teamAvatar';
import {
  TeamEventRecord,
  getTeamEventRecord,
} from '~/components/tba/teamEventAppearance';
import { Button } from '~/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
import { Input } from '~/components/ui/input';
import { getRemappedRobots } from '~/lib/eventUtils';
import { getTeamPreferredRobotPicMedium } from '~/lib/mediaUtils';
import { staleTimeForYear } from '~/lib/queryClient';
import { sortTeamsComparator } from '~/lib/teamUtils';
import { STATE_TO_ABBREVIATION, splitIntoNChunks } from '~/lib/utils';

interface EventTeamsTabProps {
  event: Event;
  teams: Team[];
  matches: Match[];
  media: Media[];
  statuses?: { [key: string]: TeamEventStatus | null };
  pitMap?: NexusPitMapData | null;
  relatedEventKeys?: string[];
}

type PitTeam = readonly [pit: string, robotNumber: string];

const NexusPitMap = lazy(() => import('~/components/tba/nexusPitMap'));

function statusesQuery(eventKey: string, year: number) {
  return {
    ...getEventTeamsStatusesOptions({ path: { event_key: eventKey } }),
    staleTime: staleTimeForYear(year),
  };
}

function nexusInfoQuery(eventKey: string) {
  return {
    ...getEventNexusInfoOptions({ path: { event_key: eventKey } }),
    staleTime: 30_000,
  };
}

function colorsQuery(eventKey: string, year: number) {
  return {
    ...getEventColorsOptions({ path: { eventKey } }),
    staleTime: staleTimeForYear(year),
  };
}

// Championship divisions publish a playoff alliance map whose pit IDs collide
// with the teams' regular pits, so only trust an event whose pits all fit.
function pitsOnMap(pits: PitTeam[], pitMap: NexusPitMapData): PitTeam[] {
  return pits.every(([pit]) => pit in pitMap.pits) ? pits : [];
}

// Nexus gives each event its own copy of a shared venue map, and copies taken
// at different times can renumber pits, so only borrow teams from an event
// whose copy puts every pit in the same place.
function samePits(a: NexusPitMapData, b: NexusPitMapData): boolean {
  const ids = Object.keys(a.pits);
  return (
    ids.length === Object.keys(b.pits).length &&
    ids.every(
      (id) =>
        a.pits[id].position?.x === b.pits[id]?.position?.x &&
        a.pits[id].position?.y === b.pits[id]?.position?.y,
    )
  );
}

function PitMap({
  event,
  pitMap,
  ownPits,
  relatedEventKeys,
}: {
  event: Event;
  pitMap: NexusPitMapData;
  ownPits: PitTeam[];
  relatedEventKeys: string[];
}) {
  const relatedInfo = useQueries({
    queries: relatedEventKeys.map(nexusInfoQuery),
  });
  const relatedStatuses = useQueries({
    queries: relatedEventKeys.map((key) => statusesQuery(key, event.year)),
  });
  const eventColors = useQueries({
    queries: [event.key, ...relatedEventKeys].map((key) =>
      colorsQuery(key, event.year),
    ),
  });
  const teamsByPit = new Map([
    ...relatedInfo.flatMap(({ data }, index): PitTeam[] => {
      const relatedMap = data?.pit_map;
      if (!relatedMap || !samePits(pitMap, relatedMap)) {
        return [];
      }
      return [
        ...Object.entries(relatedMap.pits).flatMap(([pit, { team_key }]) =>
          team_key ? [[pit, team_key.slice(3).toUpperCase()] as const] : [],
        ),
        ...pitsOnMap(
          Object.entries(relatedStatuses[index].data ?? {}).flatMap(
            ([teamKey, status]) =>
              status?.pit_location
                ? [[status.pit_location, teamKey.slice(3)] as const]
                : [],
          ),
          pitMap,
        ),
      ];
    }),
    ...pitsOnMap(ownPits, pitMap),
  ]);
  const colors: EventColors = {
    teams: eventColors.reduce<EventColors['teams']>(
      (all, { data }) => ({ ...all, ...data?.teams }),
      {},
    ),
  };
  return (
    <NexusPitMap
      pitMap={pitMap}
      year={event.year}
      teamsByPit={teamsByPit}
      colors={colors}
    />
  );
}

const ROW_TARGET_CLASS = `block text-sm wrap-break-word after:absolute
  after:inset-0 hover:underline focus-visible:[outline:2px_solid_transparent]
  focus-visible:after:outline-2 focus-visible:after:outline-ring`;

function TeamLabel({ team, robotNumber }: { team: Team; robotNumber: string }) {
  return (
    <>
      <span className="font-bold tabular-nums">{robotNumber}</span>
      {team.nickname && (
        <>
          {' '}
          <span className="font-medium">- {team.nickname}</span>
        </>
      )}
    </>
  );
}

export default function EventTeamsTab({
  event,
  teams,
  matches,
  media,
  statuses,
  pitMap,
  relatedEventKeys = [],
}: EventTeamsTabProps) {
  const { year, first_event_code: firstEventCode } = event;
  const [search, setSearch] = useState('');
  const entries = useMemo(() => {
    const byTeam = new Map<string, Media[]>();
    for (const item of media) {
      for (const key of item.team_keys) {
        const items = byTeam.get(key) ?? [];
        items.push(item);
        byTeam.set(key, items);
      }
    }
    const placeholderKeys = new Set(Object.keys(event.remap_teams ?? {}));
    return teams
      .filter((team) => !placeholderKeys.has(team.key))
      .sort(sortTeamsComparator)
      .flatMap((team) =>
        [
          { robotKey: team.key, sourceTeamKey: team.key },
          ...getRemappedRobots(event, team.key),
        ].map(({ robotKey, sourceTeamKey }) => {
          const robotNumber = robotKey.substring(3);
          const status = statuses?.[sourceTeamKey] ?? null;
          const pit = status?.pit_location;
          return {
            team,
            robotKey,
            robotNumber,
            status,
            pit,
            teamMatches: matches.filter(
              (match) =>
                match.alliances.red.team_keys.includes(robotKey) ||
                match.alliances.blue.team_keys.includes(robotKey),
            ),
            avatar: byTeam
              .get(team.key)
              ?.find(
                (item) => item.type === 'avatar' && item.details?.base64Image,
              ),
            photo: getTeamPreferredRobotPicMedium(
              byTeam.get(sourceTeamKey) ?? [],
            ),
            searchable: [
              robotNumber,
              team.nickname,
              team.city,
              team.state_prov,
              STATE_TO_ABBREVIATION.get(team.state_prov ?? ''),
              team.country,
              pit,
            ]
              .filter((value) => value != null)
              .join(' ')
              .toLowerCase(),
          };
        }),
      );
  }, [event, teams, matches, media, statuses]);
  const hasAvatars = entries.some((entry) => entry.avatar);
  const hasPits = entries.some((entry) => entry.pit);
  const ownPits = useMemo(
    () =>
      entries.flatMap(({ pit, robotKey, team, robotNumber }): PitTeam[] =>
        pit && robotKey === team.key ? [[pit, robotNumber]] : [],
      ),
    [entries],
  );
  const queryClient = useQueryClient();
  const prefetchPitMap = () => {
    relatedEventKeys.forEach((key) => {
      void queryClient.prefetchQuery(nexusInfoQuery(key));
      void queryClient.prefetchQuery(statusesQuery(key, year));
    });
    [event.key, ...relatedEventKeys].forEach(
      (key) => void queryClient.prefetchQuery(colorsQuery(key, year)),
    );
  };
  const query = search.trim().toLowerCase();
  const filtered = entries.filter((entry) => entry.searchable.includes(query));

  return (
    <section aria-label="Event teams" className="space-y-3 [&_a]:text-inherit">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="relative w-full sm:max-w-sm">
          <SearchIcon
            aria-hidden="true"
            className="pointer-events-none absolute top-2.5 left-3 size-4
              text-muted-foreground"
          />
          <Input
            type="search"
            aria-label="Search teams"
            placeholder="Search teams, locations, pits…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="pr-10 pl-9 [&::-webkit-search-cancel-button]:hidden"
          />
          {search && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Clear search"
              onClick={() => setSearch('')}
              className="absolute top-0 right-0 size-9"
            >
              <XIcon className="size-4" />
            </Button>
          )}
        </div>
        <div className="flex items-center gap-3">
          <output className="text-xs text-muted-foreground tabular-nums">
            {query
              ? `${filtered.length} of ${entries.length} teams`
              : `${entries.length} teams`}
          </output>
          {pitMap && (
            <Dialog>
              <DialogTrigger
                render={<Button size="sm" variant="outline" />}
                onPointerEnter={prefetchPitMap}
                onFocus={prefetchPitMap}
              >
                <MapIcon />
                Pit map
              </DialogTrigger>
              <DialogContent
                aria-describedby={undefined}
                focusContentOnOpen
                className="max-h-[90vh] grid-rows-[auto_minmax(0,1fr)_auto]
                  sm:max-w-5xl"
              >
                <DialogHeader>
                  <DialogTitle>Pit map</DialogTitle>
                </DialogHeader>
                <div className="min-h-0 overflow-auto rounded-md border">
                  <Suspense
                    fallback={
                      <LoadingSkeleton
                        label="Loading pit map"
                        className="aspect-square w-full"
                      />
                    }
                  >
                    <PitMap
                      event={event}
                      pitMap={pitMap}
                      ownPits={ownPits}
                      relatedEventKeys={relatedEventKeys}
                    />
                  </Suspense>
                </div>
                {firstEventCode && (
                  <a
                    href={`https://frc.nexus/en/event/${year}${firstEventCode}/map`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-muted-foreground hover:underline"
                  >
                    Pit map data from frc.nexus
                  </a>
                )}
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>
      {filtered.length === 0 ? (
        <p className="border-y py-8 text-center text-sm text-muted-foreground">
          {entries.length === 0
            ? 'No teams listed'
            : 'No teams match your search'}
        </p>
      ) : (
        <div
          className="grid
            grid-cols-[repeat(auto-fit,minmax(min(100%,25rem),1fr))] gap-x-6"
        >
          {splitIntoNChunks(filtered, 2).map((chunk, index) => (
            <ul key={index} className="divide-y border-b lg:border-t">
              {chunk.map(
                ({
                  team,
                  robotKey,
                  robotNumber,
                  status,
                  pit,
                  teamMatches,
                  avatar,
                  photo,
                }) => (
                  <li
                    key={robotKey}
                    className="relative isolate flex min-h-14 items-center gap-2
                      py-1 hover:bg-muted/50"
                  >
                    {hasAvatars && (
                      <div className="size-12 shrink-0">
                        <TeamAvatar
                          media={avatar?.type === 'avatar' ? avatar : undefined}
                          className="relative z-10"
                        />
                      </div>
                    )}
                    <div className="min-w-0 flex-1 py-1">
                      {teamMatches.length > 0 ? (
                        <Dialog>
                          <DialogTrigger
                            className={`${ROW_TARGET_CLASS} cursor-pointer
                              text-left`}
                          >
                            <TeamLabel team={team} robotNumber={robotNumber} />
                          </DialogTrigger>
                          <DialogContent
                            aria-describedby={undefined}
                            className="max-h-[90vh] overflow-y-auto
                              sm:max-w-3xl"
                          >
                            <DialogHeader>
                              <DialogTitle>
                                <TeamLink teamOrKey={team.key} year={year}>
                                  Team {robotNumber}
                                  {team.nickname ? ` — ${team.nickname}` : ''}
                                </TeamLink>
                              </DialogTitle>
                            </DialogHeader>
                            <TeamEventRecord
                              event={event}
                              teamKey={robotKey}
                              status={status}
                              record={getTeamEventRecord(
                                event,
                                robotKey,
                                teamMatches,
                              )}
                            />
                            <SimpleMatchRowsWithBreaks
                              matches={teamMatches}
                              event={event}
                              breakers={[
                                START_OF_QUALS_BREAKER,
                                END_OF_DAY_BREAKER,
                                CHANGE_IN_COMP_LEVEL_BREAKER,
                              ]}
                              focusTeamKeys={[robotKey]}
                            />
                          </DialogContent>
                        </Dialog>
                      ) : (
                        <TeamLink
                          teamOrKey={team.key}
                          year={year}
                          className={ROW_TARGET_CLASS}
                        >
                          <TeamLabel team={team} robotNumber={robotNumber} />
                        </TeamLink>
                      )}
                      <div
                        className="flex flex-wrap items-baseline gap-x-3 text-xs
                          text-muted-foreground"
                      >
                        {(team.city || team.state_prov || team.country) && (
                          <span className="relative z-10">
                            <TeamLocationLink team={team} />
                          </span>
                        )}
                        {hasPits && (
                          <span
                            className={
                              pit && firstEventCode
                                ? 'relative z-10 shrink-0'
                                : 'shrink-0'
                            }
                          >
                            Pit{' '}
                            {pit && firstEventCode ? (
                              <PitLocationLink
                                teamNumber={team.team_number}
                                year={year}
                                firstEventCode={firstEventCode}
                                pitLocation={pit}
                              />
                            ) : (
                              pit || '—'
                            )}
                          </span>
                        )}
                      </div>
                    </div>
                    {photo && (
                      <Dialog>
                        <DialogTrigger
                          aria-label={`View robot photo for team ${robotNumber}`}
                          className="relative z-10 shrink-0 cursor-pointer
                            rounded-md focus-visible:outline-2
                            focus-visible:outline-ring"
                        >
                          <img
                            src={photo}
                            alt={`Team ${robotNumber} robot`}
                            loading="lazy"
                            className="size-12 rounded-md object-cover"
                          />
                        </DialogTrigger>
                        <DialogContent aria-describedby={undefined}>
                          <DialogHeader>
                            <DialogTitle>
                              <TeamLink teamOrKey={team.key} year={year}>
                                Team {robotNumber}
                                {team.nickname ? ` — ${team.nickname}` : ''}
                              </TeamLink>
                            </DialogTitle>
                          </DialogHeader>
                          <img
                            src={photo}
                            alt={`Team ${robotNumber} robot`}
                            className="max-h-[80vh] w-full rounded-md
                              object-contain"
                          />
                        </DialogContent>
                      </Dialog>
                    )}
                  </li>
                ),
              )}
            </ul>
          ))}
        </div>
      )}
    </section>
  );
}
