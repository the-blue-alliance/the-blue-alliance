import { Temporal } from 'temporal-polyfill';
import { describe, expect, test } from 'vitest';

import type { Event, Match } from '~/api/tba/read';
import { CompLevel } from '~/api/tba/read';
import { buildEventFeed, formatRfc2822 } from '~/lib/eventFeed';

const NOW = Temporal.Instant.from('2024-03-09T15:04:05Z');

function makeEvent(name: string = 'Silicon Valley Regional'): Event {
  return {
    key: '2024casj',
    name,
    year: 2024,
    playoff_type: null,
  } as Event;
}

function makeMatch(
  key: string,
  compLevel: CompLevel,
  setNumber: number,
  matchNumber: number,
  redScore: number = 100,
  blueScore: number = 80,
): Match {
  return {
    key,
    comp_level: compLevel,
    set_number: setNumber,
    match_number: matchNumber,
    alliances: {
      red: {
        score: redScore,
        team_keys: ['frc254', 'frc1678', 'frc2056'],
      },
      blue: {
        score: blueScore,
        team_keys: ['frc604', 'frc1323', 'frc2910B'],
      },
    },
  } as Match;
}

function itemTitles(feed: string): string[] {
  return [...feed.matchAll(/<item>\n<title>(.*)<\/title>/g)].map(
    (found) => found[1],
  );
}

describe('formatRfc2822', () => {
  test('formats an instant in UTC', () => {
    expect(formatRfc2822(NOW)).toBe('Sat, 09 Mar 2024 15:04:05 +0000');
  });
});

describe('buildEventFeed', () => {
  test('titles the channel with the event name and year', () => {
    expect(buildEventFeed(makeEvent(), [], NOW)).toContain(
      '<title>Silicon Valley Regional 2024</title>',
    );
  });

  test('links the channel to the event page', () => {
    expect(buildEventFeed(makeEvent(), [], NOW)).toContain(
      '<link>https://www.thebluealliance.com/event/2024casj</link>',
    );
  });

  test('stamps the channel with the build time', () => {
    expect(buildEventFeed(makeEvent(), [], NOW)).toContain(
      '<lastBuildDate>Sat, 09 Mar 2024 15:04:05 +0000</lastBuildDate>',
    );
  });

  test('escapes special characters in the event name', () => {
    expect(buildEventFeed(makeEvent('Rock & Roll <Open>'), [], NOW)).toContain(
      '<title>Rock &amp; Roll &lt;Open&gt; 2024</title>',
    );
  });

  test('links each item to its match page', () => {
    const feed = buildEventFeed(
      makeEvent(),
      [makeMatch('2024casj_qm1', CompLevel.QM, 1, 1)],
      NOW,
    );
    expect(feed).toContain(
      '<guid>https://www.thebluealliance.com/match/2024casj_qm1</guid>',
    );
  });

  test('lists both alliances with scores and bare team numbers', () => {
    const feed = buildEventFeed(
      makeEvent(),
      [makeMatch('2024casj_qm1', CompLevel.QM, 1, 1, 120, 95)],
      NOW,
    );
    expect(feed).toContain(
      '<![CDATA[<h1>Red Alliance: 120</h1><li>254</li><li>1678</li><li>2056</li><h1>Blue Alliance: 95</h1><li>604</li><li>1323</li><li>2910B</li>]]>',
    );
  });

  test('omits unplayed matches', () => {
    const feed = buildEventFeed(
      makeEvent(),
      [makeMatch('2024casj_qm1', CompLevel.QM, 1, 1, -1, -1)],
      NOW,
    );
    expect(itemTitles(feed)).toEqual([]);
  });

  test('omits practice matches', () => {
    const feed = buildEventFeed(
      makeEvent(),
      [makeMatch('2024casj_pm1', CompLevel.PM, 1, 1)],
      NOW,
    );
    expect(itemTitles(feed)).toEqual([]);
  });

  test('orders matches from qualifications through finals', () => {
    const feed = buildEventFeed(
      makeEvent(),
      [
        makeMatch('2024casj_f1m1', CompLevel.F, 1, 1),
        makeMatch('2024casj_sf1m1', CompLevel.SF, 1, 1),
        makeMatch('2024casj_qm2', CompLevel.QM, 1, 2),
        makeMatch('2024casj_qf1m1', CompLevel.QF, 1, 1),
        makeMatch('2024casj_qm1', CompLevel.QM, 1, 1),
      ],
      NOW,
    );
    expect(itemTitles(feed)).toEqual([
      'Quals 1',
      'Quals 2',
      'Quarters 1 Match 1',
      'Semis 1 Match 1',
      'Finals 1',
    ]);
  });
});
