import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  type Event,
  EventType,
  type Team,
  type TeamEventStatus,
} from '~/api/tba/read';
import {
  TeamStatus,
  getTotalRankingPoints,
} from '~/components/tba/teamEventAppearance';

const event = {
  event_type: EventType.REGIONAL,
  key: '2026test',
  year: 2026,
} as Event;

const status = {
  qual: {
    ranking: {
      matches_played: 12,
      rank: null,
      record: { wins: 8, losses: 4, ties: 0 },
      sort_orders: [3],
    },
    sort_order_info: [{ name: 'Ranking Score', precision: 2 }],
  },
} satisfies TeamEventStatus;

describe('getTotalRankingPoints', () => {
  test('converts an average ranking score to total ranking points', () => {
    expect(getTotalRankingPoints(event, status)).toBe(36);
  });

  test('preserves a ranking score that is already a total', () => {
    const totalStatus = {
      qual: {
        ranking: { matches_played: 12, sort_orders: [39] },
        sort_order_info: [{ name: 'Ranking Score', precision: 0 }],
      },
    } satisfies TeamEventStatus;

    expect(getTotalRankingPoints(event, totalStatus)).toBe(39);
  });

  test('omits ranking points when ranking score metadata is unavailable', () => {
    const statusWithoutRankingScore = {
      qual: {
        ranking: { matches_played: 12, sort_orders: [3] },
        sort_order_info: [],
      },
    } satisfies TeamEventStatus;

    expect(
      getTotalRankingPoints(event, statusWithoutRankingScore),
    ).toBeUndefined();
  });
});

describe('TeamStatus', () => {
  test('shows total ranking points below the team record', () => {
    render(
      <TeamStatus
        event={event}
        status={status}
        team={{ key: 'frc254' } as Team}
        awards={[]}
        maybeDistrictPoints={null}
        maybeRegionalPoolPoints={null}
        maybeAlliances={null}
      />,
    );

    expect(screen.getByText('36 RP')).toBeTruthy();
  });
});
