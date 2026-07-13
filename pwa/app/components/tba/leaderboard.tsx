import { Link } from '@tanstack/react-router';
import { Fragment, type ReactNode } from 'react';

import MaterialSymbolsTrophy from '~icons/material-symbols/trophy';

import { InsightCard } from '~/components/tba/insightCard';
import { MatchLink, TeamLink } from '~/components/tba/links';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import {
  PRE_EXPANDED_ROWS,
  rankRowClassName,
  rankTextClassName,
} from '~/lib/insightUtils';
import { cn, pluralize } from '~/lib/utils';

const MAX_KEYS_PER_ROW = 20;

type KeyType = 'team' | 'event' | 'match' | 'team_pair' | 'alliance';

const KEY_TYPE_HEADER: Record<KeyType, string> = {
  team: 'Team',
  event: 'Event',
  match: 'Match',
  team_pair: 'Team Pair',
  alliance: 'Alliance',
};

type LeaderboardContext =
  | { event_keys?: Array<string> }
  | { match_key: string; alliance: Array<string> };

export interface LeaderboardData {
  key_type: KeyType;
  rankings: Array<{
    keys: Array<string> | Array<Array<string>>;
    value: number;
    contexts?: Array<LeaderboardContext>;
  }>;
}

export interface LeaderboardShape {
  name: string;
  year: number;
  data: LeaderboardData;
}

export function Leaderboard({
  subtitle,
  leaderboard,
  displayName: displayNameProp,
  contextTooltipMap,
  year,
  renderKey,
}: {
  subtitle?: string;
  leaderboard: LeaderboardShape;
  displayName?: string;
  contextTooltipMap?: Record<string, ReactNode>;
  year: number;
  renderKey?: (key: string) => ReactNode;
}) {
  const displayName = displayNameProp ?? leaderboard.name;

  return (
    <InsightCard
      icon={MaterialSymbolsTrophy}
      title={displayName}
      subtitle={subtitle}
    >
      {(expanded) => (
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-10 w-[4.5rem] text-center font-semibold">
                Count
              </TableHead>
              <TableHead className="h-10 text-left font-semibold">
                {KEY_TYPE_HEADER[leaderboard.data.key_type]}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {leaderboard.data.rankings
              .slice(0, expanded ? 100 : PRE_EXPANDED_ROWS)
              .map((r, i) => {
                const rank = i + 1;

                return (
                  <TableRow
                    key={i}
                    className={cn(
                      'transition-colors hover:bg-muted/50',
                      rankRowClassName(rank),
                    )}
                  >
                    <TableCell
                      className={cn(
                        'text-center font-semibold numeric-data',
                        rank <= 3 && 'text-base',
                        rankTextClassName(rank),
                      )}
                    >
                      {r.value}
                    </TableCell>
                    <TableCell className="py-3 pl-4 text-left">
                      <LeaderboardKeyList
                        cutoffSize={MAX_KEYS_PER_ROW}
                        keyType={leaderboard.data.key_type}
                        keyVals={r.keys}
                        contexts={r.contexts}
                        contextTooltipMap={contextTooltipMap}
                        year={year}
                        renderKey={renderKey}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      )}
    </InsightCard>
  );
}

/**
 * Normalizes a ranking's `keys` (which may be a flat list, or a list of
 * grouped keys for `team_pair`/`alliance` key types) into a flat list of
 * entries, each either a single key or a group of keys rendered together.
 */
function normalizeKeyEntries(
  keyVals: Array<string> | Array<Array<string>>,
): Array<string | Array<string>> {
  return keyVals;
}

function entryToId(entry: string | Array<string>): string {
  return Array.isArray(entry) ? entry.join('-') : entry;
}

function LeaderboardKeyList({
  keyVals,
  keyType,
  cutoffSize,
  contexts,
  contextTooltipMap,
  year,
  renderKey,
}: {
  keyType: KeyType;
  keyVals: Array<string> | Array<Array<string>>;
  cutoffSize: number;
  contexts?: Array<LeaderboardContext>;
  contextTooltipMap?: Record<string, ReactNode>;
  year: number;
  renderKey?: (key: string) => ReactNode;
}) {
  const entries = normalizeKeyEntries(keyVals);

  return (
    <>
      {entries.slice(0, cutoffSize).map((entry, i) => (
        <Fragment key={entryToId(entry)}>
          {i > 0 && ', '}
          <LeaderboardKeyTooltip
            keyType={keyType}
            entry={entry}
            year={year}
            renderKey={renderKey}
            context={contexts?.[i]}
            contextTooltipMap={contextTooltipMap}
          />
        </Fragment>
      ))}
      {entries.length > cutoffSize && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger className="italic">
              &nbsp;(and{' '}
              {pluralize(entries.length - cutoffSize, 'other', 'others')})
            </TooltipTrigger>
            <TooltipContent
              className="max-w-[500px] text-center break-words
                whitespace-normal"
            >
              <p>
                {entries.map((entry, i) => (
                  <Fragment key={entryToId(entry)}>
                    {i > 0 && ', '}
                    <LeaderboardKeyGroupLink
                      keyType={keyType}
                      entry={entry}
                      year={year}
                      renderKey={renderKey}
                    />
                  </Fragment>
                ))}
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </>
  );
}

function LeaderboardKeyTooltip({
  keyType,
  entry,
  year,
  renderKey,
  context,
  contextTooltipMap,
}: {
  keyType: KeyType;
  entry: string | Array<string>;
  year: number;
  renderKey?: (key: string) => ReactNode;
  context?: LeaderboardContext;
  contextTooltipMap?: Record<string, ReactNode>;
}) {
  const tooltipContent = context
    ? contextFromLeaderboardContext(context)
    : (contextTooltipMap?.[entryToId(entry)] ?? null);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger>
          <LeaderboardKeyGroupLink
            keyType={keyType}
            entry={entry}
            year={year}
            renderKey={renderKey}
          />
        </TooltipTrigger>
        {tooltipContent ? (
          <TooltipContent>
            <p>{tooltipContent}</p>
          </TooltipContent>
        ) : null}
      </Tooltip>
    </TooltipProvider>
  );
}

function contextFromLeaderboardContext(context: LeaderboardContext): ReactNode {
  if ('match_key' in context) {
    return (
      <>
        <MatchLink matchOrKey={context.match_key}>
          {context.match_key}
        </MatchLink>
        {context.alliance.length > 0 && (
          <>
            {' '}
            (
            {context.alliance.map((teamKey, i) => (
              <Fragment key={teamKey}>
                {i > 0 && ', '}
                <TeamLink teamOrKey={teamKey} year={0}>
                  {teamKey.substring(3)}
                </TeamLink>
              </Fragment>
            ))}
            )
          </>
        )}
      </>
    );
  }

  if (!context.event_keys || context.event_keys.length === 0) {
    return null;
  }

  return (
    <>
      {context.event_keys.map((eventKey, i) => (
        <Fragment key={eventKey}>
          {i > 0 && ', '}
          <Link to="/event/$eventKey" params={{ eventKey }}>
            {eventKey}
          </Link>
        </Fragment>
      ))}
    </>
  );
}

/**
 * Renders a single entry, which is either one key or (for `team_pair`/
 * `alliance` key types) a group of keys joined together.
 */
function LeaderboardKeyGroupLink({
  entry,
  keyType,
  year,
  renderKey,
}: {
  keyType: KeyType;
  entry: string | Array<string>;
  year: number;
  renderKey?: (key: string) => ReactNode;
}) {
  if (!Array.isArray(entry)) {
    return (
      <LeaderboardKeyLink
        keyType={keyType}
        keyVal={entry}
        year={year}
        renderKey={renderKey}
      />
    );
  }

  const separator = keyType === 'team_pair' ? ' & ' : ', ';

  return (
    <>
      {entry.map((k, i) => (
        <Fragment key={k}>
          {i > 0 && separator}
          <LeaderboardKeyLink
            keyType={keyType}
            keyVal={k}
            year={year}
            renderKey={renderKey}
          />
        </Fragment>
      ))}
    </>
  );
}

function LeaderboardKeyLink({
  keyVal,
  keyType,
  year,
  renderKey,
}: {
  keyType: KeyType;
  keyVal: string;
  year: number;
  renderKey?: (key: string) => ReactNode;
}) {
  if (renderKey) {
    return <>{renderKey(keyVal)}</>;
  }
  if (keyType === 'team' || keyType === 'team_pair' || keyType === 'alliance') {
    return (
      <TeamLink teamOrKey={keyVal} year={year}>
        {keyVal.substring(3)}
      </TeamLink>
    );
  }
  if (keyType === 'event') {
    return (
      <Link to="/event/$eventKey" params={{ eventKey: keyVal }}>
        {keyVal}
      </Link>
    );
  }
  if (keyType === 'match') {
    return <MatchLink matchOrKey={keyVal}>{keyVal}</MatchLink>;
  }
}
