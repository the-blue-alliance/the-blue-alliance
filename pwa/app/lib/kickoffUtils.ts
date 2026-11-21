import { Temporal } from 'temporal-polyfill';

const KICKOFF_TIMEZONE = 'America/New_York';
const WINDOW_OPENS_MONTH = 11;
const WINDOW_CLOSES_AFTER = Temporal.Duration.from({ days: 1 });

export function getKickoffCountdownTarget(
  kickoffDatetime: string | undefined,
  now: Temporal.Instant,
): Temporal.ZonedDateTime | null {
  if (!kickoffDatetime) {
    return null;
  }

  let kickoff: Temporal.ZonedDateTime;
  try {
    kickoff =
      Temporal.Instant.from(kickoffDatetime).toZonedDateTimeISO(
        KICKOFF_TIMEZONE,
      );
  } catch {
    return null;
  }

  const windowEnd = kickoff.add(WINDOW_CLOSES_AFTER).toInstant();
  if (Temporal.Instant.compare(now, windowEnd) > 0) {
    return null;
  }

  const windowStart = Temporal.ZonedDateTime.from({
    timeZone: KICKOFF_TIMEZONE,
    year: kickoff.year - 1,
    month: WINDOW_OPENS_MONTH,
    day: 1,
  }).toInstant();
  if (Temporal.Instant.compare(now, windowStart) < 0) {
    return null;
  }

  return kickoff;
}
