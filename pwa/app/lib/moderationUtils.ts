import { Temporal } from 'temporal-polyfill';

// Queue display order, matching the web review home
// (suggestions/pending_suggestion_rows_partial.html)
export const SUGGESTION_TYPE_ORDER = [
  'match',
  'event',
  'media',
  'social-media',
  'event_media',
  'robot',
  'offseason-event',
  'api_auth_access',
];

export function suggestionTypeOrderComparator(a: string, b: string): number {
  const indexOf = (type: string) => {
    const index = SUGGESTION_TYPE_ORDER.indexOf(type);
    return index === -1 ? SUGGESTION_TYPE_ORDER.length : index;
  };
  return indexOf(a) - indexOf(b);
}

/**
 * Groups suggestions by their target key, preserving the order in which
 * targets first appear. Used to cluster webcast suggestions per event like
 * the web review page.
 */
export function groupSuggestionsByTargetKey<
  T extends { target_key?: string | null },
>(suggestions: T[]): { targetKey: string; suggestions: T[] }[] {
  const groups = new Map<string, T[]>();
  for (const suggestion of suggestions) {
    const key = suggestion.target_key ?? '';
    const group = groups.get(key);
    if (group) {
      group.push(suggestion);
    } else {
      groups.set(key, [suggestion]);
    }
  }
  return [...groups.entries()].map(([targetKey, grouped]) => ({
    targetKey,
    suggestions: grouped,
  }));
}

/** "Mar 24 – Mar 27" for an event's start/end dates, or undefined. */
export function formatEventDateRange(
  startDate: string | null | undefined,
  endDate: string | null | undefined,
): string | undefined {
  if (!startDate || !endDate) return undefined;
  const format = (date: string) =>
    Temporal.PlainDate.from(date).toLocaleString('default', {
      month: 'short',
      day: 'numeric',
    });
  return `${format(startDate)} – ${format(endDate)}`;
}

/**
 * Sanity-checks a social media suggestion's foreign key for a given media
 * slug. Returns a human-readable warning when the value is not a plain
 * profile identifier — e.g. Facebook personal-profile/group links instead of
 * Page usernames, or YouTube video links instead of channels.
 */
export function socialProfileWarning(
  slug: string | null | undefined,
  foreignKey: string,
): string | undefined {
  if (!foreignKey) return undefined;
  const urlJunk = /https?:|www\.|[?=&%#\s]/i.test(foreignKey);
  switch (slug) {
    case 'facebook-profile': {
      if (/profile\.php/i.test(foreignKey)) {
        return 'This is a personal profile link (profile.php), not a Facebook Page username';
      }
      if (/^(groups|people|pg|pages)\b/i.test(foreignKey)) {
        return 'This is a Facebook group/profile path, not a Page username';
      }
      if (
        urlJunk ||
        /facebook\.com/i.test(foreignKey) ||
        foreignKey.includes('/')
      ) {
        return 'Not a plain Facebook Page username';
      }
      if (/^\d+$/.test(foreignKey)) {
        return 'Numeric Facebook ID — verify this is a Page, not a personal profile';
      }
      return undefined;
    }
    case 'youtube-channel': {
      if (/watch|youtu\.be|shorts[/]|playlist|v=/i.test(foreignKey)) {
        return 'This links to a YouTube video, not a channel';
      }
      const validChannel =
        /^@[\w.-]+$/.test(foreignKey) ||
        /^channel\/UC[\w-]{22}$/.test(foreignKey) ||
        /^(c|user)\/[\w.-]+$/.test(foreignKey) ||
        /^[\w.-]+$/.test(foreignKey);
      if (urlJunk || !validChannel) {
        return 'Not a YouTube channel handle or ID';
      }
      return undefined;
    }
    case 'instagram-profile':
      return /^[A-Za-z0-9._]+$/.test(foreignKey)
        ? undefined
        : 'Not a plain Instagram username';
    case 'twitter-profile':
      return /^[A-Za-z0-9_]{1,15}$/.test(foreignKey)
        ? undefined
        : 'Not a plain X handle';
    case 'github-profile':
      return /^[A-Za-z0-9-]+$/.test(foreignKey)
        ? undefined
        : 'Not a plain GitHub username';
    default:
      return undefined;
  }
}

/**
 * One-line summary of a review submission for the confirmation toast, e.g.
 * "5 accepted · 3 rejected". Returns undefined when nothing was processed.
 */
export function summarizeReviewOutcomes(result: {
  accepted: string[];
  rejected: string[];
  alreadyReviewed: string[];
}): string | undefined {
  const parts: string[] = [];
  if (result.accepted.length > 0)
    parts.push(`${result.accepted.length} accepted`);
  if (result.rejected.length > 0)
    parts.push(`${result.rejected.length} rejected`);
  if (result.alreadyReviewed.length > 0) {
    parts.push(
      `${result.alreadyReviewed.length} already reviewed by someone else`,
    );
  }
  return parts.length > 0 ? parts.join(' · ') : undefined;
}

/**
 * Reputation line for a suggestion author, e.g. "234 accepted · 12 rejected"
 * or "first-time suggester". Undefined when counts aren't available.
 */
export function formatAuthorReputation(author: {
  accepted_count?: number;
  rejected_count?: number;
}): string | undefined {
  const accepted = author.accepted_count;
  const rejected = author.rejected_count;
  if (accepted === undefined || rejected === undefined) return undefined;
  if (accepted === 0 && rejected === 0) return 'first-time suggester';
  return `${accepted} accepted · ${rejected} rejected`;
}

const MATCH_KEY_PATTERN = /^(qm|ef|qf|sf|f)(\d+)(?:m(\d+))?$/;

/** Normalize for fuzzy title comparison: lowercase, punctuation → spaces. */
function normalizeTitle(value: string): string {
  return ` ${value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()} `;
}

/** Tokens a video title might use to refer to a match, per comp level. */
function matchTokens(compLevel: string, set: number, num: number): string[] {
  switch (compLevel) {
    case 'qm':
      return [
        `qm${set}`,
        `q${set}`,
        `qual ${set}`,
        `quals ${set}`,
        `qualification ${set}`,
        `qualification match ${set}`,
        `match ${set}`,
      ];
    case 'ef':
      return [`ef${set}m${num}`, `octofinal ${set}`, `eighth final ${set}`];
    case 'qf':
      return [
        `qf${set}m${num}`,
        `qf${set}`,
        `quarterfinal ${set}`,
        `quarter final ${set}`,
      ];
    case 'sf':
      // Double-elim (2023+) semifinal keys are also called "Playoff Match N"
      return [
        `sf${set}m${num}`,
        `sf${set}`,
        `semifinal ${set}`,
        `semi final ${set}`,
        `playoff ${set}`,
        `playoff match ${set}`,
        `match ${set}`,
      ];
    case 'f':
      return [
        `f${set}m${num}`,
        `final ${num}`,
        `finals ${num}`,
        `final`,
        `finals`,
      ];
    default:
      return [];
  }
}

const EVENT_NAME_STOPWORDS = new Set([
  'first',
  'frc',
  'robotics',
  'competition',
  'event',
  'presented',
]);

/**
 * Yellow-flag a suggested match video whose YouTube title doesn't appear to
 * reference the target match or its event. Assistive only — moderators
 * should still watch the video.
 */
export function matchVideoTitleWarning(
  videoTitle: string | null | undefined,
  targetKey: string | null | undefined,
  event?: { name?: string | null; year?: number | null } | null,
): string | undefined {
  if (!videoTitle || !targetKey) return undefined;
  const title = normalizeTitle(videoTitle);
  const [eventKey, matchPart] = targetKey.split('_');
  if (!matchPart) return undefined;
  const parsed = MATCH_KEY_PATTERN.exec(matchPart.toLowerCase());
  if (!parsed) return undefined;
  const [, compLevel, setStr, numStr] = parsed;
  const tokens = matchTokens(compLevel, Number(setStr), Number(numStr ?? '1'));
  const mentionsMatch = tokens.some((token) =>
    token.includes(' ') ? title.includes(` ${token} `) : title.includes(token),
  );
  if (mentionsMatch) return undefined;

  const eventTokens = new Set<string>();
  if (event?.year) eventTokens.add(String(event.year));
  const eventCode = eventKey.replace(/^\d+/, '');
  if (eventCode.length >= 3) eventTokens.add(eventCode);
  for (const word of normalizeTitle(event?.name ?? '').split(' ')) {
    if (word.length >= 4 && !EVENT_NAME_STOPWORDS.has(word)) {
      eventTokens.add(word);
    }
  }
  const mentionsEvent = [...eventTokens].some((token) =>
    title.includes(` ${token} `),
  );
  if (mentionsEvent) {
    return `Title doesn't mention ${matchPart.toUpperCase()} — verify it shows this match`;
  }
  return "Title doesn't mention this match or event — verify it's the right video";
}

// A single FRC match video runs a few minutes; anything past this without a
// timestamp is almost certainly a full-stream upload
const LONG_VIDEO_THRESHOLD_SECONDS = 20 * 60;

/**
 * Yellow-flag a long suggested video with no timestamp pointing at the
 * match within the stream.
 */
export function matchVideoDurationWarning(
  durationSeconds: number | null | undefined,
  rawVideoId: string,
): string | undefined {
  if (!durationSeconds || durationSeconds <= LONG_VIDEO_THRESHOLD_SECONDS) {
    return undefined;
  }
  const hasTimestamp = /[?&#]t=\d|[?&]start=\d/.test(rawVideoId);
  if (hasTimestamp) return undefined;
  const minutes = Math.round(durationSeconds / 60);
  return `Video is ${minutes} minutes long with no timestamp — looks like a full-stream upload, check that it starts at this match`;
}

/**
 * Whether "add as preferred team image" should default to checked: yes for
 * images when the team has no preferred images yet.
 */
export function defaultSetPreferred(suggestion: {
  candidate_media?: { is_image?: boolean } | null;
  existing_preferred?: unknown[] | null;
}): boolean {
  const isImage = suggestion.candidate_media?.is_image ?? false;
  return isImage && (suggestion.existing_preferred ?? []).length === 0;
}

/**
 * Default expiration for an accepted API write key, mirroring the backend:
 * event end + 7 days while that date is still in the future, never otherwise.
 */
export function defaultExpirationDays(
  eventEndDate: string | null | undefined,
  today: Temporal.PlainDate = Temporal.Now.plainDateISO(),
): number {
  if (!eventEndDate) return -1;
  const endPlus7 = Temporal.PlainDate.from(eventEndDate).add({ days: 7 });
  return Temporal.PlainDate.compare(endPlus7, today) >= 0 ? 7 : -1;
}
