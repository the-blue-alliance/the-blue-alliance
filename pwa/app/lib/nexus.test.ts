import { describe, expect, it } from 'vitest';

import type { NexusEventInfo, NexusMatchInfo } from '~/api/tba/read';
import { buildNexusStatusMap } from '~/lib/nexus';

function match(
  status: NexusMatchInfo['status'],
  played = false,
): NexusMatchInfo {
  return {
    label: 'Qualification 1',
    status,
    played,
    times: { estimated_queue_time_ms: null, estimated_start_time_ms: null },
  };
}

function eventInfo(matches: NexusEventInfo['matches']): NexusEventInfo {
  return { data_as_of_ms: 0, now_queueing: null, matches };
}

describe('buildNexusStatusMap', () => {
  it('returns empty map for null/undefined status', () => {
    expect(buildNexusStatusMap(null)).toEqual({});
    expect(buildNexusStatusMap(undefined)).toEqual({});
  });

  it('returns empty map when there are no matches', () => {
    expect(buildNexusStatusMap(eventInfo({}))).toEqual({});
  });

  it('maps the three active queuing statuses', () => {
    const status = eventInfo({
      '2024casf_qm7': match('Now queuing'),
      '2024casf_qm8': match('On deck'),
      '2024casf_qm9': match('On field'),
    });
    expect(buildNexusStatusMap(status)).toEqual({
      '2024casf_qm7': 'Now queuing',
      '2024casf_qm8': 'On deck',
      '2024casf_qm9': 'On field',
    });
  });

  it("skips 'Queuing soon' matches (noise — nearly every upcoming match)", () => {
    const status = eventInfo({
      '2024casf_qm6': match('Queuing soon'),
      '2024casf_qm7': match('Now queuing'),
    });
    expect(buildNexusStatusMap(status)).toEqual({
      '2024casf_qm7': 'Now queuing',
    });
  });

  it('skips played matches', () => {
    const status = eventInfo({
      '2024casf_qm5': match('On field', true),
      '2024casf_qm6': match('On deck'),
    });
    expect(buildNexusStatusMap(status)).toEqual({
      '2024casf_qm6': 'On deck',
    });
  });
});
