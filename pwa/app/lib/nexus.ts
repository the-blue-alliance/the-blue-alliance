import { queryOptions } from '@tanstack/react-query';
import { createServerFn } from '@tanstack/react-start';

import { pullLiveEventStatus } from '~/api/nexus/sdk.gen';
import type { EventStatus } from '~/api/nexus/types.gen';
import { createLogger } from '~/lib/utils';

export type NexusMatchStatus = 'Now queuing' | 'On deck' | 'On field';

function nexusLabelToTbaKey(eventKey: string, label: string): string | null {
  const qualMatch = label.match(/^Qualification (\d+)(?:\s+Replay)?$/);
  const finalMatch = label.match(/^Final (\d+)$/);
  const playoffMatch = label.match(/^Playoff (\d+)$/);

  if (qualMatch) return `${eventKey}_qm${qualMatch[1]}`;
  if (finalMatch) return `${eventKey}_f1m${finalMatch[1]}`;
  if (playoffMatch) return `${eventKey}_sf1m${playoffMatch[1]}`;
  return null;
}

export function buildNexusStatusMap(
  eventKey: string,
  status: EventStatus | null | undefined,
): Record<string, NexusMatchStatus> {
  if (!status?.matches) return {};

  const result: Record<string, NexusMatchStatus> = {};
  const onFieldMatches: Array<{
    key: string;
    onFieldTime: number | null;
    index: number;
  }> = [];

  for (let index = 0; index < status.matches.length; index++) {
    const match = status.matches[index];
    if (!match.status || !match.label) continue;
    if (
      match.status !== 'Now queuing' &&
      match.status !== 'On deck' &&
      match.status !== 'On field'
    )
      continue;

    const key = nexusLabelToTbaKey(eventKey, match.label);
    if (!key) continue;

    result[key] = match.status;
    if (match.status === 'On field') {
      onFieldMatches.push({
        key,
        onFieldTime:
          match.times?.actualOnFieldTime ??
          match.times?.estimatedOnFieldTime ??
          null,
        index,
      });
    }
  }

  if (onFieldMatches.length > 1) {
    const latestOnField = onFieldMatches.reduce((latest, current) => {
      const latestTime = latest.onFieldTime ?? Number.NEGATIVE_INFINITY;
      const currentTime = current.onFieldTime ?? Number.NEGATIVE_INFINITY;

      if (currentTime > latestTime) return current;
      if (currentTime < latestTime) return latest;
      return current.index > latest.index ? current : latest;
    });

    for (const onFieldMatch of onFieldMatches) {
      if (onFieldMatch.key !== latestOnField.key) {
        delete result[onFieldMatch.key];
      }
    }
  }

  return result;
}

const logger = createLogger('nexus');

/**
 * Core handler logic for fetching Nexus live event status.
 * Exported separately to allow unit testing without createServerFn's RPC layer.
 */
export async function fetchNexusEventStatusHandler(
  eventKey: string,
): Promise<EventStatus | null> {
  const apiKey = process.env.NEXUS_API_KEY;
  if (!apiKey) {
    logger.warn('NEXUS_API_KEY not set — skipping Nexus live event status');
    return null;
  }

  // Allow a demo event key override for local development/testing.
  // Set NEXUS_DEMO_EVENT_KEY to a Nexus demo key (e.g. demo2750) to test
  // the integration without a live event.
  const effectiveKey = process.env.NEXUS_DEMO_EVENT_KEY || eventKey;

  const response = await pullLiveEventStatus({
    path: { eventKey: effectiveKey },
    headers: { 'Nexus-Api-Key': apiKey },
    throwOnError: true,
  }).catch((err: unknown) => {
    logger.warn(
      { err, eventKey: effectiveKey },
      'Failed to fetch Nexus event status',
    );
    return null;
  });

  return response?.data ?? null;
}

export const fetchNexusEventStatus = createServerFn({ method: 'GET' })
  .inputValidator((eventKey: string) => eventKey)
  .handler(({ data: eventKey }) => fetchNexusEventStatusHandler(eventKey));

export const getNexusEventStatusQueryKey = (eventKey: string) =>
  ['nexusEventStatus', eventKey] as const;

export const getNexusEventStatusOptions = (eventKey: string) =>
  queryOptions({
    queryKey: getNexusEventStatusQueryKey(eventKey),
    queryFn: () => fetchNexusEventStatus({ data: eventKey }),
    staleTime: 30_000,
    retry: false,
  });
