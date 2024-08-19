import { describe, expect, test } from 'vitest';

import { Event } from '~/api/v3';
import { getEventDateString, getEventWeekString } from '~/lib/eventUtils';

describe.concurrent('getEventDateString', () => {
  test('Same start and end date', () => {
    // @ts-ignore
    const event: Event = {
      key: '2024test',
      name: 'Test Event',
      start_date: '2024-01-01',
      end_date: '2024-01-01',
    };
    expect(getEventDateString(event, 'short')).toEqual('Jan 1, 2024');
  });

  test('Different start and end dates', () => {
    // @ts-ignore
    const event: Event = {
      key: '2024test',
      name: 'Test Event',
      start_date: '2024-01-01',
      end_date: '2024-01-03',
    };
    expect(getEventDateString(event, 'short')).toEqual('Jan 1 to Jan 3, 2024');
  });

  test('Different month start and end dates', () => {
    // @ts-ignore
    const event: Event = {
      key: '2024test',
      name: 'Test Event',
      start_date: '2024-03-30',
      end_date: '2024-04-01',
    };
    expect(getEventDateString(event, 'short')).toEqual('Mar 30 to Apr 1, 2024');
  });
});

describe.concurrent('getEventWeekString', () => {
  test('Null year', () => {
    // @ts-ignore
    const event: Event = {
      year: 2024,
      week: null,
    };
    expect(getEventWeekString(event)).toEqual(null);
  });

  test('Nominal case', () => {
    // @ts-ignore
    const event: Event = {
      year: 2024,
      week: 0,
    };
    expect(getEventWeekString(event)).toEqual('Week 1');
  });

  test('2016 special case', () => {
    // @ts-ignore
    const event1: Event = {
      year: 2016,
      week: 0,
    };
    expect(getEventWeekString(event1)).toEqual('Week 0.5');

    // @ts-ignore
    const event2: Event = {
      year: 2016,
      week: 1,
    };
    expect(getEventWeekString(event2)).toEqual('Week 1');
  });

  test('2021 special case: Participation', () => {
    // @ts-ignore
    const event: Event = {
      year: 2021,
      week: 0,
    };
    expect(getEventWeekString(event)).toEqual('Participation');
  });

  test('2021 special case: Innovation', () => {
    // @ts-ignore
    const event: Event = {
      year: 2021,
      week: 6,
    };
    expect(getEventWeekString(event)).toEqual('FIRST Innovation Challenge');
  });

  test('2021 special case: IR@H', () => {
    // @ts-ignore
    const event: Event = {
      year: 2021,
      week: 7,
    };
    expect(getEventWeekString(event)).toEqual(
      'INFINITE RECHARGE At Home Challenge',
    );
  });

  test('2021 special case: GDC', () => {
    // @ts-ignore
    const event: Event = {
      year: 2021,
      week: 8,
    };
    expect(getEventWeekString(event)).toEqual('Game Design Challenge');
  });

  test('2021 special case: Awards', () => {
    // @ts-ignore
    const event: Event = {
      year: 2021,
      week: 9,
    };
    expect(getEventWeekString(event)).toEqual('Awards');
  });
});
