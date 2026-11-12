const KNOWN_DISTRICT_ABBREVIATIONS = new Set([
  'chs',
  'fch',
  'fim',
  'fit',
  'tx',
  'in',
  'fin',
  'isr',
  'mar',
  'fma',
  'nc',
  'fnc',
  'fsc',
  'ne',
  'ont',
  'pnw',
  'pch',
  'ca',
  'win',
]);

// Same patterns as the Jinja short routes in src/backend/web/main.py. Team numbers are
// digits only, event and district keys need a letter after the year, so "/2024" is a team.
const TEAM_NUMBER_PATTERN = /^[0-9]{1,5}$/;
const EVENT_OR_DISTRICT_PATTERN = /^([0-9]{4})([a-z][a-z0-9]*)$/;

export type ShortKeyTarget =
  | { type: 'team'; teamNumber: string }
  | { type: 'district'; abbreviation: string; year: string }
  | { type: 'event'; eventKey: string };

export function resolveShortKey(key: string): ShortKeyTarget | null {
  if (TEAM_NUMBER_PATTERN.test(key)) {
    return { type: 'team', teamNumber: String(Number(key)) };
  }

  const match = EVENT_OR_DISTRICT_PATTERN.exec(key);
  if (!match) {
    return null;
  }

  const [, year, suffix] = match;
  if (KNOWN_DISTRICT_ABBREVIATIONS.has(suffix)) {
    return { type: 'district', abbreviation: suffix, year };
  }
  return { type: 'event', eventKey: key };
}
