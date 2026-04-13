import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { pullLiveEventStatus } from '~/api/nexus/sdk.gen';
import type { EventStatus } from '~/api/nexus/types.gen';
import { buildNexusStatusMap, fetchNexusEventStatusHandler } from '~/lib/nexus';

// Mock the Nexus SDK before importing the handler
vi.mock('~/api/nexus/sdk.gen', () => ({
  pullLiveEventStatus: vi.fn(),
}));

// Mock the logger to suppress output
vi.mock('~/lib/utils', async (importOriginal) => {
  const actual = await importOriginal<typeof import('~/lib/utils')>();
  return {
    ...actual,
    createLogger: () => ({
      warn: vi.fn(),
      info: vi.fn(),
      error: vi.fn(),
    }),
  };
});

const mockPullLiveEventStatus = vi.mocked(pullLiveEventStatus);

const sampleStatus: EventStatus = {
  eventKey: '2024casf',
  dataAsOfTime: 1716598570773,
  nowQueuing: 'Qualification 6',
  matches: [
    {
      label: 'Qualification 6',
      status: 'Now queuing',
      redTeams: ['1000', '2000', '3000'],
      blueTeams: ['4000', '5000', '6000'],
      times: { estimatedQueueTime: 1716598570000 },
    },
  ],
  announcements: [],
  partsRequests: [],
};

describe('fetchNexusEventStatusHandler', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset both env vars to a clean state before each test
    vi.stubEnv('NEXUS_API_KEY', '');
    vi.stubEnv('NEXUS_DEMO_EVENT_KEY', '');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('returns null and warns when NEXUS_API_KEY is not set', async () => {
    vi.stubEnv('NEXUS_API_KEY', '');

    const result = await fetchNexusEventStatusHandler('2024casf');

    expect(result).toBeNull();
    expect(mockPullLiveEventStatus).not.toHaveBeenCalled();
  });

  it('returns event status when API key is set', async () => {
    vi.stubEnv('NEXUS_API_KEY', 'test-api-key');
    mockPullLiveEventStatus.mockResolvedValueOnce({
      data: sampleStatus,
    } as Awaited<ReturnType<typeof pullLiveEventStatus>>);

    const result = await fetchNexusEventStatusHandler('2024casf');

    expect(result).toEqual(sampleStatus);
    expect(mockPullLiveEventStatus).toHaveBeenCalledWith({
      path: { eventKey: '2024casf' },
      headers: { 'Nexus-Api-Key': 'test-api-key' },
      throwOnError: true,
    });
  });

  it('uses NEXUS_DEMO_EVENT_KEY override when set', async () => {
    vi.stubEnv('NEXUS_API_KEY', 'test-api-key');
    vi.stubEnv('NEXUS_DEMO_EVENT_KEY', 'demo2750');
    mockPullLiveEventStatus.mockResolvedValueOnce({
      data: sampleStatus,
    } as Awaited<ReturnType<typeof pullLiveEventStatus>>);

    await fetchNexusEventStatusHandler('2024casf');

    expect(mockPullLiveEventStatus).toHaveBeenCalledWith(
      expect.objectContaining({ path: { eventKey: 'demo2750' } }),
    );
  });

  it('returns null when the API call throws', async () => {
    vi.stubEnv('NEXUS_API_KEY', 'test-api-key');
    mockPullLiveEventStatus.mockRejectedValueOnce(new Error('404 Not Found'));

    const result = await fetchNexusEventStatusHandler('2024unknownevent');

    expect(result).toBeNull();
  });

  it('returns null when the response has no data', async () => {
    vi.stubEnv('NEXUS_API_KEY', 'test-api-key');
    mockPullLiveEventStatus.mockResolvedValueOnce(
      null as unknown as Awaited<ReturnType<typeof pullLiveEventStatus>>,
    );

    const result = await fetchNexusEventStatusHandler('2024casf');

    expect(result).toBeNull();
  });
});

describe('buildNexusStatusMap', () => {
  it('returns empty map for null status', () => {
    expect(buildNexusStatusMap('2024casf', null)).toEqual({});
  });

  it('returns empty map for status with no matches', () => {
    expect(
      buildNexusStatusMap('2024casf', {
        eventKey: '2024casf',
        dataAsOfTime: 0,
      } as EventStatus),
    ).toEqual({});
  });

  it('maps qualification matches correctly', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [
        { label: 'Qualification 6', status: 'Now queuing' },
        { label: 'Qualification 7', status: 'On deck' },
        { label: 'Qualification 8', status: 'On field' },
      ],
    };
    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_qm6': 'Now queuing',
      '2024casf_qm7': 'On deck',
      '2024casf_qm8': 'On field',
    });
  });

  it('maps final matches correctly', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [{ label: 'Final 2', status: 'On field' }],
    };
    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_f1m2': 'On field',
    });
  });

  it('maps playoff matches correctly', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [{ label: 'Playoff 3', status: 'On deck' }],
    };
    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_sf1m3': 'On deck',
    });
  });

  it('skips non-active statuses', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [
        { label: 'Qualification 1', status: 'Queuing soon' },
        { label: 'Qualification 2', status: 'On field' },
      ],
    };
    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_qm2': 'On field',
    });
  });

  it('skips practice and unknown match labels', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [
        { label: 'Practice 1', status: 'On field' },
        { label: 'Qualification 5', status: 'On deck' },
      ],
    };
    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_qm5': 'On deck',
    });
  });

  it('handles qualification replay labels', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [{ label: 'Qualification 4 Replay', status: 'On field' }],
    };
    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_qm4': 'On field',
    });
  });

  it('keeps only the most recent on-field match', () => {
    const status: EventStatus = {
      eventKey: '2024casf',
      dataAsOfTime: 0,
      matches: [
        {
          label: 'Qualification 8',
          status: 'On field',
          times: { actualOnFieldTime: 1_000 },
        },
        {
          label: 'Qualification 9',
          status: 'On field',
          times: { actualOnFieldTime: 2_000 },
        },
        { label: 'Qualification 10', status: 'On deck' },
      ],
    };

    expect(buildNexusStatusMap('2024casf', status)).toEqual({
      '2024casf_qm9': 'On field',
      '2024casf_qm10': 'On deck',
    });
  });
});
