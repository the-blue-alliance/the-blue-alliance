import { describe, expect, test } from 'vitest';

import { type Award, AwardType, type Event } from '~/api/tba/read';
import { sortAwardsByEventDate, sortAwardsComparator } from '~/lib/awardUtils';

function award(awardType: AwardType, eventKey = '2024casj'): Award {
  return {
    name: '',
    award_type: awardType,
    event_key: eventKey,
    recipient_list: [],
    year: 2024,
  };
}

function event(key: string, startDate: string): Event {
  // @ts-expect-error: Don't need to fill out all the fields
  return { key, start_date: startDate };
}

describe('sortAwardsComparator', () => {
  test('orders the Impact award before the event winner', () => {
    const sorted = [award(AwardType.WINNER), award(AwardType.CHAIRMANS)].sort(
      sortAwardsComparator,
    );

    expect(sorted.map((a) => a.award_type)).toEqual([
      AwardType.CHAIRMANS,
      AwardType.WINNER,
    ]);
  });

  test('orders unlisted awards after listed ones, by award type', () => {
    const sorted = [
      award(AwardType.AUTONOMOUS),
      award(AwardType.SAFETY),
      award(AwardType.FINALIST),
    ].sort(sortAwardsComparator);

    expect(sorted.map((a) => a.award_type)).toEqual([
      AwardType.FINALIST,
      AwardType.SAFETY,
      AwardType.AUTONOMOUS,
    ]);
  });
});

describe('sortAwardsByEventDate', () => {
  test('orders awards by the start date of their event', () => {
    const events = [event('2024b', '2024-03-08'), event('2024a', '2024-03-01')];
    const awards = [
      award(AwardType.WINNER, '2024b'),
      award(AwardType.WINNER, '2024a'),
    ];

    expect(
      sortAwardsByEventDate(awards, events).map((a) => a.event_key),
    ).toEqual(['2024a', '2024b']);
  });

  test('falls back to award order when an event is unknown', () => {
    const events = [event('2024a', '2024-03-01')];
    const awards = [
      award(AwardType.WINNER, '2024unknown'),
      award(AwardType.CHAIRMANS, '2024a'),
    ];

    expect(
      sortAwardsByEventDate(awards, events).map((a) => a.award_type),
    ).toEqual([AwardType.CHAIRMANS, AwardType.WINNER]);
  });
});
