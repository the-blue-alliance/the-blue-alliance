import { useMemo, useState } from 'react';

import SearchIcon from '~icons/lucide/search';
import XIcon from '~icons/lucide/x';

import type {
  Event,
  Match,
  Media,
  Team,
  TeamEventStatus,
} from '~/api/tba/read';
import {
  PitLocationLink,
  TeamLink,
  TeamLocationLink,
} from '~/components/tba/links';
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
import { getTeamPreferredRobotPicMedium } from '~/lib/mediaUtils';
import { sortTeamsComparator } from '~/lib/teamUtils';
import { STATE_TO_ABBREVIATION, splitIntoNChunks } from '~/lib/utils';

interface EventTeamsTabProps {
  event: Event;
  teams: Team[];
  matches: Match[];
  media: Media[];
  statuses?: { [key: string]: TeamEventStatus | null };
}

const ROW_TARGET_CLASS = `block text-sm wrap-break-word after:absolute
  after:inset-0 hover:underline focus-visible:[outline:2px_solid_transparent]
  focus-visible:after:outline-2 focus-visible:after:outline-ring`;

function TeamLabel({ team }: { team: Team }) {
  return (
    <>
      <span className="font-bold tabular-nums">{team.team_number}</span>
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
    return [...teams].sort(sortTeamsComparator).map((team) => {
      const teamMedia = byTeam.get(team.key) ?? [];
      const pit = statuses?.[team.key]?.pit_location;
      return {
        team,
        pit,
        teamMatches: matches.filter(
          (match) =>
            match.alliances.red.team_keys.includes(team.key) ||
            match.alliances.blue.team_keys.includes(team.key),
        ),
        avatar: teamMedia.find(
          (item) => item.type === 'avatar' && item.details?.base64Image,
        ),
        photo: getTeamPreferredRobotPicMedium(teamMedia),
        searchable: [
          team.team_number,
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
    });
  }, [teams, matches, media, statuses]);
  const hasAvatars = entries.some((entry) => entry.avatar);
  const hasPits = entries.some((entry) => entry.pit);
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
        <output className="text-xs text-muted-foreground tabular-nums">
          {query
            ? `${filtered.length} of ${teams.length} teams`
            : `${teams.length} teams`}
        </output>
      </div>
      {filtered.length === 0 ? (
        <p className="border-y py-8 text-center text-sm text-muted-foreground">
          {teams.length === 0
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
              {chunk.map(({ team, pit, teamMatches, avatar, photo }) => (
                <li
                  key={team.key}
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
                          <TeamLabel team={team} />
                        </DialogTrigger>
                        <DialogContent
                          aria-describedby={undefined}
                          className="max-h-[90vh] overflow-y-auto sm:max-w-3xl"
                        >
                          <DialogHeader>
                            <DialogTitle>
                              <TeamLink teamOrKey={team.key} year={year}>
                                Team {team.team_number}
                                {team.nickname ? ` — ${team.nickname}` : ''}
                              </TeamLink>
                            </DialogTitle>
                          </DialogHeader>
                          <TeamEventRecord
                            event={event}
                            teamKey={team.key}
                            status={statuses?.[team.key] ?? null}
                            record={getTeamEventRecord(
                              event,
                              team.key,
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
                            focusTeamKey={team.key}
                          />
                        </DialogContent>
                      </Dialog>
                    ) : (
                      <TeamLink
                        teamOrKey={team.key}
                        year={year}
                        className={ROW_TARGET_CLASS}
                      >
                        <TeamLabel team={team} />
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
                        aria-label={`View robot photo for team ${team.team_number}`}
                        className="relative z-10 shrink-0 cursor-pointer
                          rounded-md focus-visible:outline-2
                          focus-visible:outline-ring"
                      >
                        <img
                          src={photo}
                          alt={`Team ${team.team_number} robot`}
                          loading="lazy"
                          className="size-12 rounded-md object-cover"
                        />
                      </DialogTrigger>
                      <DialogContent aria-describedby={undefined}>
                        <DialogHeader>
                          <DialogTitle>
                            <TeamLink teamOrKey={team.key} year={year}>
                              Team {team.team_number}
                              {team.nickname ? ` — ${team.nickname}` : ''}
                            </TeamLink>
                          </DialogTitle>
                        </DialogHeader>
                        <img
                          src={photo}
                          alt={`Team ${team.team_number} robot`}
                          className="max-h-[80vh] w-full rounded-md
                            object-contain"
                        />
                      </DialogContent>
                    </Dialog>
                  )}
                </li>
              ))}
            </ul>
          ))}
        </div>
      )}
    </section>
  );
}
