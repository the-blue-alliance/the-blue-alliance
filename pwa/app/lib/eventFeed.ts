import { Temporal } from 'temporal-polyfill';

import { CompLevel, Event, Match, MatchAlliance } from '~/api/tba/read';
import {
  matchHasBeenPlayed,
  matchTitleShort,
  sortMatchComparator,
} from '~/lib/matchUtils';

const SITE_URL = 'https://www.thebluealliance.com';
const CONTACT_EMAIL = 'contact@thebluealliance.com';
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const MONTH_NAMES = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];
const XML_ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&apos;',
};

function escapeXml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => XML_ESCAPES[char] ?? char);
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}

export function formatRfc2822(instant: Temporal.Instant): string {
  const utc = instant.toZonedDateTimeISO('UTC');
  const date = `${DAY_NAMES[utc.dayOfWeek - 1]}, ${pad(utc.day)} ${MONTH_NAMES[utc.month - 1]} ${utc.year}`;
  const time = `${pad(utc.hour)}:${pad(utc.minute)}:${pad(utc.second)}`;
  return `${date} ${time} +0000`;
}

function allianceHtml(label: string, alliance: MatchAlliance): string {
  const teams = alliance.team_keys
    .map((teamKey) => `<li>${teamKey.replace(/^frc/, '')}</li>`)
    .join('');
  return `<h1>${label} Alliance: ${alliance.score}</h1>${teams}`;
}

function matchItem(match: Match, event: Event): string {
  const url = `${SITE_URL}/match/${match.key}`;
  const description =
    allianceHtml('Red', match.alliances.red) +
    allianceHtml('Blue', match.alliances.blue);
  return `<item>
<title>${escapeXml(matchTitleShort(match, event.playoff_type))}</title>
<link>${url}</link>
<guid>${url}</guid>
<description><![CDATA[${description}]]></description>
</item>`;
}

export function buildEventFeed(
  event: Event,
  matches: Match[],
  now: Temporal.Instant,
): string {
  const name = escapeXml(`${event.name} ${event.year}`);
  const date = formatRfc2822(now);
  const items = matches
    .filter(
      (match) => match.comp_level !== CompLevel.PM && matchHasBeenPlayed(match),
    )
    .sort(sortMatchComparator)
    .map((match) => matchItem(match, event))
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
<title>${name}</title>
<link>${SITE_URL}/event/${event.key}</link>
<description>RSS feed for the ${escapeXml(event.name)} provided by The Blue Alliance.</description>
<language>en-us</language>
<pubDate>${date}</pubDate>
<lastBuildDate>${date}</lastBuildDate>
<generator>The Blue Alliance</generator>
<managingEditor>${CONTACT_EMAIL}</managingEditor>
<webMaster>${CONTACT_EMAIL}</webMaster>
${items}
</channel>
</rss>
`;
}
