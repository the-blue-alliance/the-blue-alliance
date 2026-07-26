import type { NexusEventInfo, NexusMatchInfo } from '~/api/tba/read';

// 'Queuing soon' applies to essentially every not-yet-played match, so it's
// noise on the results table — we only surface the three active queuing states.
export type NexusMatchStatus = Exclude<
  NexusMatchInfo['status'],
  'Queuing soon'
>;

export function buildNexusStatusMap(
  status: NexusEventInfo | null | undefined,
): Record<string, NexusMatchStatus> {
  if (!status?.matches) return {};

  const result: Record<string, NexusMatchStatus> = {};
  for (const [matchKey, match] of Object.entries(status.matches)) {
    if (match.played || match.status === 'Queuing soon') continue;
    result[matchKey] = match.status;
  }

  return result;
}
