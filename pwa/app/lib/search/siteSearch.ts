import MiniSearch from 'minisearch';

import { SearchIndex } from '~/api/tba/read';

type SearchableTeam = SearchIndex['teams'][number];
type SearchableEvent = SearchIndex['events'][number];

export interface SearchResult {
  type: 'team' | 'event';
  key: string;
  label: string;
  path: string;
}

interface TeamDocument {
  id: string;
  type: 'team';
  code: string;
  name: string;
  team: SearchableTeam;
}

interface EventDocument {
  id: string;
  type: 'event';
  code: string;
  name: string;
  event: SearchableEvent;
}

type SearchDocument = TeamDocument | EventDocument;

interface SearchEngine {
  miniSearch: MiniSearch<SearchDocument>;
  documents: Map<string, SearchDocument>;
  eventsByCode: Map<string, SearchableEvent[]>;
}

const RESULT_LIMIT = 10;
const FIRST_SEASON = 1992;
const TEAM_BOOST = 1.5;
const RECENCY_HALF_LIFE = 7.5;
const TEAM_PREFIX = /^(?:frc|team)\s*(?=\d)/;
const TEAM_YEAR_PATTERN = /^(\d+)[\s/]+(\d{4})$/;
const YEAR_PATTERN = /^\d{4}$/;

const engines = new WeakMap<SearchIndex, SearchEngine>();

const eventYear = (event: SearchableEvent) => Number(event.key.substring(0, 4));
const eventCode = (event: SearchableEvent) => event.key.substring(4);
const teamKey = (teamNumber: string) => `frc${Number(teamNumber)}`;

function buildEngine(index: SearchIndex): SearchEngine {
  const documents = new Map<string, SearchDocument>([
    ...index.teams.map((team): [string, TeamDocument] => [
      team.key,
      {
        id: team.key,
        type: 'team',
        code: team.key.substring(3),
        name: team.nickname,
        team,
      },
    ]),
    ...index.events.map((event): [string, EventDocument] => [
      event.key,
      {
        id: event.key,
        type: 'event',
        code: eventCode(event),
        name: event.name,
        event,
      },
    ]),
  ]);

  const eventsByCode = new Map<string, SearchableEvent[]>();
  for (const event of index.events.toSorted(
    (a, b) => eventYear(a) - eventYear(b),
  )) {
    eventsByCode.set(eventCode(event), [
      ...(eventsByCode.get(eventCode(event)) ?? []),
      event,
    ]);
  }

  const miniSearch = new MiniSearch<SearchDocument>({
    fields: ['code', 'name'],
  });
  miniSearch.addAll([...documents.values()]);

  return { miniSearch, documents, eventsByCode };
}

function getEngine(index: SearchIndex): SearchEngine {
  const cached = engines.get(index);
  if (cached) {
    return cached;
  }
  const engine = buildEngine(index);
  engines.set(index, engine);
  return engine;
}

function teamResult(team: SearchableTeam, year?: number): SearchResult {
  const teamNumber = team.key.substring(3);
  const label = `${teamNumber} - ${team.nickname}`;
  const path = `/team/${teamNumber}`;
  return year === undefined
    ? { type: 'team', key: team.key, label, path }
    : {
        type: 'team',
        key: team.key,
        label: `${label} (${year})`,
        path: `${path}/${year}`,
      };
}

function eventResult(event: SearchableEvent): SearchResult {
  return {
    type: 'event',
    key: event.key,
    label: `${eventYear(event)} ${event.name.trim()} [${eventCode(event)}]`,
    path: `/event/${event.key}`,
  };
}

function documentResult(
  doc: SearchDocument | undefined,
  year?: number,
): SearchResult | undefined {
  if (doc?.type === 'team') {
    return teamResult(doc.team, year);
  }
  return doc && (year === undefined || eventYear(doc.event) === year)
    ? eventResult(doc.event)
    : undefined;
}

function exactCodeEvent(
  events: SearchableEvent[] | undefined,
  currentSeason: number,
  year?: number,
): SearchableEvent | undefined {
  if (year !== undefined) {
    return events?.find((e) => eventYear(e) === year);
  }
  return events?.findLast((e) => eventYear(e) <= currentSeason) ?? events?.[0];
}

function documentBoost(
  doc: SearchDocument | undefined,
  currentSeason: number,
): number {
  if (doc?.type !== 'event') {
    return TEAM_BOOST;
  }
  const age = currentSeason - eventYear(doc.event);
  return age < 0 ? 1 : 1 + 1 / (1 + age / RECENCY_HALF_LIFE);
}

function splitYear(
  query: string,
  currentSeason: number,
): { terms: string; year?: number } {
  const tokens = query.split(/\s+/);
  const yearIndex = tokens.findIndex(
    (t) =>
      YEAR_PATTERN.test(t) &&
      Number(t) >= FIRST_SEASON &&
      Number(t) <= currentSeason + 1,
  );
  if (tokens.length < 2 || yearIndex === -1) {
    return { terms: query };
  }
  return {
    terms: tokens.toSpliced(yearIndex, 1).join(' '),
    year: Number(tokens[yearIndex]),
  };
}

export function siteSearch(
  index: SearchIndex,
  rawQuery: string,
  currentSeason: number,
): SearchResult[] {
  const engine = getEngine(index);
  const query = rawQuery.trim().toLowerCase().replace(TEAM_PREFIX, '');
  if (!query) {
    return [];
  }

  const teamYear = TEAM_YEAR_PATTERN.exec(query);
  const teamYearDoc = teamYear && engine.documents.get(teamKey(teamYear[1]));
  if (teamYear && teamYearDoc?.type === 'team') {
    return [teamResult(teamYearDoc.team, Number(teamYear[2]))];
  }

  const { terms, year } = splitYear(query, currentSeason);
  const exactEvent = engine.documents.get(query);
  const exactTeam = /^\d+$/.test(terms)
    ? engine.documents.get(teamKey(terms))
    : undefined;
  const exactCode = exactCodeEvent(
    engine.eventsByCode.get(terms),
    currentSeason,
    year,
  );

  const hits = engine.miniSearch.search(terms, {
    prefix: true,
    fuzzy: (term) => (term.length >= 5 && !/\d/.test(term) ? 0.2 : false),
    combineWith: 'AND',
    bm25: { k: 1.2, b: 0, d: 0.5 },
    boostDocument: (id) =>
      documentBoost(engine.documents.get(String(id)), currentSeason),
  });

  const pinned = [
    exactEvent?.type === 'event' ? eventResult(exactEvent.event) : undefined,
    documentResult(exactTeam, year),
    exactCode && eventResult(exactCode),
  ].filter((r) => r !== undefined);
  const results = new Map(pinned.map((r) => [r.path, r]));
  for (const hit of hits) {
    if (results.size >= RESULT_LIMIT) {
      break;
    }
    const result = documentResult(engine.documents.get(String(hit.id)), year);
    if (result && !results.has(result.path)) {
      results.set(result.path, result);
    }
  }
  return [...results.values()];
}
