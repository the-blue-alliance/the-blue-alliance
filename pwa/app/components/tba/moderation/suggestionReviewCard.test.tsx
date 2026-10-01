import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { Temporal } from 'temporal-polyfill';
import { describe, expect, test, vi } from 'vitest';

import type {
  AcceptRequest,
  ModerationSuggestion,
} from '~/api/tba/moderation/types.gen';
import { SuggestionType } from '~/api/tba/moderation/types.gen';
import { EventType } from '~/api/tba/read';
import {
  type ReviewDecision,
  SuggestionReviewCard,
  suggestedEventType,
} from '~/components/tba/moderation/suggestionReviewCard';
import { formatEventDateRange } from '~/lib/moderationUtils';

vi.mock('@tanstack/react-router', () => ({
  Link: ({
    children,
    params,
    to,
    ...props
  }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
    children: ReactNode;
    params?: Record<string, string>;
    to: string;
  }) => (
    <a
      href={Object.entries(params ?? {}).reduce(
        (href, [key, value]) => href.replace(`$${key}`, value),
        to,
      )}
      {...props}
    >
      {children}
    </a>
  ),
}));

vi.mock('~/components/tba/videoEmbeds', () => ({
  YoutubeEmbed: ({ videoId, title }: { videoId: string; title: string }) => (
    <div data-testid="youtube-embed" data-video-id={videoId}>
      {title}
    </div>
  ),
}));

vi.mock('react-social-media-embed', () => ({
  InstagramEmbed: ({ url }: { url: string }) => (
    <div data-testid="instagram-embed">{url}</div>
  ),
}));

const OFFSEASON_SUGGESTION = {
  key: 'offseason-1',
  target_model: SuggestionType.OFFSEASON_EVENT,
  contents: {
    name: 'Chezy Champs',
    start_date: '2026-09-25',
    end_date: '2026-09-27',
    venue_name: 'Bellarmine College Preparatory',
    address: '960 W Hedding St',
    city: 'San Jose',
    state: 'CA',
    country: 'USA',
    website: 'https://cheesyarena.com',
  },
} as unknown as ModerationSuggestion;

// Relative to today so the timing badge is deterministic without faking
// the clock, which the Temporal polyfill would not see anyway.
const EVENT_START = Temporal.Now.plainDateISO().add({ days: 5 });
const EVENT_END = EVENT_START.add({ days: 3 });

const API_WRITE_SUGGESTION = {
  key: 'apiwrite-1',
  target_model: SuggestionType.API_AUTH_ACCESS,
  contents: { event_key: '2026casj', affiliation: 'Team 254' },
  event: {
    type: 'event',
    key: '2026casj',
    name: 'Silicon Valley Regional',
    year: 2026,
    start_date: EVENT_START.toString(),
    end_date: EVENT_END.toString(),
  },
  requested_auth_types: [{ type: 3, name: 'event matches' }],
} as unknown as ModerationSuggestion;

function renderCard(suggestion: ModerationSuggestion) {
  return render(
    <SuggestionReviewCard
      suggestion={suggestion}
      decision={undefined}
      onDecisionChange={() => {}}
      overrides={{}}
      onOverridesChange={() => {}}
    />,
  );
}

describe('SuggestionReviewCard api write request', () => {
  test('shows the event dates and how far off the event is', () => {
    renderCard(API_WRITE_SUGGESTION);

    expect(
      screen.getByText(
        `(${formatEventDateRange(EVENT_START.toString(), EVENT_END.toString())})`,
      ),
    ).toBeDefined();
    expect(screen.getByText('Starts in 5 days')).toBeDefined();
  });

  test('omits the dates when the event has none', () => {
    renderCard({
      ...API_WRITE_SUGGESTION,
      event: {
        ...API_WRITE_SUGGESTION.event,
        start_date: null,
        end_date: null,
      },
    } as unknown as ModerationSuggestion);

    expect(screen.queryByText(/Starts in|Happening now|Ended/)).toBeNull();
    expect(screen.queryByText(/\(.* – .*\)/)).toBeNull();
  });
});

describe('SuggestionReviewCard offseason event', () => {
  test('defaults the event type select to the type the suggestion carries', () => {
    const preseason = {
      ...OFFSEASON_SUGGESTION,
      contents: { ...OFFSEASON_SUGGESTION.contents, event_type: 100 },
    } as unknown as ModerationSuggestion;
    render(
      <SuggestionReviewCard
        suggestion={preseason}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{}}
        onOverridesChange={() => {}}
      />,
    );

    const select = screen.getByLabelText('Event type') as HTMLSelectElement;
    expect(Number(select.value)).toBe(EventType.PRESEASON);
  });

  test('defaults the event type select to Offseason when the suggestion has no type', () => {
    render(
      <SuggestionReviewCard
        suggestion={OFFSEASON_SUGGESTION}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{}}
        onOverridesChange={() => {}}
      />,
    );

    const select = screen.getByLabelText('Event type') as HTMLSelectElement;
    expect(Number(select.value)).toBe(EventType.OFFSEASON);
    expect(
      Array.from(select.options).map((option) => option.textContent),
    ).toEqual(['Offseason', 'Preseason']);
  });

  test('choosing Preseason sends event_type_enum as a number', () => {
    const onOverridesChange = vi.fn<(overrides: AcceptRequest) => void>();
    render(
      <SuggestionReviewCard
        suggestion={OFFSEASON_SUGGESTION}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{ event_short: 'cc' }}
        onOverridesChange={onOverridesChange}
      />,
    );

    fireEvent.change(screen.getByLabelText('Event type'), {
      target: { value: String(EventType.PRESEASON) },
    });

    expect(onOverridesChange).toHaveBeenCalledWith({
      event_short: 'cc',
      event_type_enum: EventType.PRESEASON,
    });
  });

  test('shows the moderator override once chosen', () => {
    render(
      <SuggestionReviewCard
        suggestion={OFFSEASON_SUGGESTION}
        decision={undefined}
        onDecisionChange={() => {}}
        overrides={{ event_type_enum: EventType.PRESEASON }}
        onOverridesChange={() => {}}
      />,
    );

    const select = screen.getByLabelText('Event type') as HTMLSelectElement;
    expect(Number(select.value)).toBe(EventType.PRESEASON);
  });
});

describe('suggestedEventType', () => {
  test('reads the preseason marker and falls back to offseason', () => {
    expect(suggestedEventType('100')).toBe(EventType.PRESEASON);
    expect(suggestedEventType('99')).toBe(EventType.OFFSEASON);
    expect(suggestedEventType('')).toBe(EventType.OFFSEASON);
  });
});

function suggestionOf(fields: Record<string, unknown>): ModerationSuggestion {
  return {
    key: 's-1',
    contents: {},
    ...fields,
  } as unknown as ModerationSuggestion;
}

function renderWith(
  suggestion: ModerationSuggestion,
  props: {
    decision?: ReviewDecision;
    overrides?: AcceptRequest;
    hideEventContext?: boolean;
    focused?: boolean;
  } = {},
) {
  const onDecisionChange = vi.fn<(decision: ReviewDecision) => void>();
  const onOverridesChange = vi.fn<(overrides: AcceptRequest) => void>();
  const result = render(
    <SuggestionReviewCard
      suggestion={suggestion}
      decision={props.decision}
      onDecisionChange={onDecisionChange}
      overrides={props.overrides ?? {}}
      onOverridesChange={onOverridesChange}
      hideEventContext={props.hideEventContext}
      focused={props.focused}
    />,
  );
  return { ...result, onDecisionChange, onOverridesChange };
}

function fieldValue(label: string) {
  return screen.getByText(`${label}:`).nextElementSibling?.textContent;
}

const TEAM_REFERENCE = {
  type: 'team',
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
};

const EVENT_REFERENCE = {
  type: 'event',
  key: '2026casj',
  name: 'Silicon Valley Regional',
  year: 2026,
};

describe('SuggestionReviewCard footer and decisions', () => {
  test('credits the author with date and reputation', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.ROBOT,
        created: '2026-03-01T12:00:00',
        author: {
          nickname: 'Scout',
          email: 'scout@example.com',
          accepted_count: 3,
          rejected_count: 1,
        },
      }),
    );

    expect(
      screen.getByText(
        'Suggested by Scout (scout@example.com) on 2026-03-01 · 3 accepted · 1 rejected',
      ),
    ).toBeTruthy();
  });

  test('credits an unknown author without extras', () => {
    renderWith(suggestionOf({ target_model: SuggestionType.ROBOT }));

    expect(screen.getByText('Suggested by unknown')).toBeTruthy();
  });

  test('toggles accept and reject', () => {
    const { onDecisionChange } = renderWith(
      suggestionOf({ target_model: 'unknown-type' }),
    );

    fireEvent.click(screen.getByRole('button', { name: '(a)ccept' }));
    fireEvent.click(screen.getByRole('button', { name: '(r)eject' }));

    expect(onDecisionChange.mock.calls).toEqual([['accept'], ['reject']]);
  });

  test('clears a decision when its button is clicked again', () => {
    const accepted = renderWith(
      suggestionOf({ target_model: 'unknown-type' }),
      { decision: 'accept' },
    );
    fireEvent.click(screen.getByRole('button', { name: '(a)ccept' }));
    expect(accepted.onDecisionChange).toHaveBeenCalledWith(undefined);
    expect(
      screen.getByRole('button', { name: '(a)ccept' }).className,
    ).toContain('bg-green-700');
    accepted.unmount();

    const rejected = renderWith(
      suggestionOf({ target_model: 'unknown-type' }),
      { decision: 'reject' },
    );
    fireEvent.click(screen.getByRole('button', { name: '(r)eject' }));
    expect(rejected.onDecisionChange).toHaveBeenCalledWith(undefined);
    expect(
      screen.getByRole('button', { name: '(r)eject' }).className,
    ).toContain('bg-red-700');
  });

  test('marks the decision and keyboard focus on the card', () => {
    renderWith(suggestionOf({ key: 'x', target_model: 'unknown-type' }), {
      decision: 'reject',
      focused: true,
    });

    const card = screen.getByTestId('suggestion-x');
    expect(card.dataset.decision).toBe('reject');
    expect(card.dataset.focused).toBe('true');
    expect(card.className).toContain('ring-2');
  });
});

describe('SuggestionReviewCard reference header', () => {
  test('links a team to the suggestion year', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.ROBOT,
        reference: TEAM_REFERENCE,
        contents: { year: 2026 },
      }),
    );

    const link = screen.getByRole('link', {
      name: 'Team 254 - The Cheesy Poofs (2026)',
    });
    expect(link.getAttribute('href')).toBe('/team/254/{-2026}');
  });

  test('links a team without a year', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.SOCIAL_MEDIA,
        reference: { ...TEAM_REFERENCE, team_number: undefined },
      }),
    );

    expect(
      screen.getByRole('link', { name: 'Team - The Cheesy Poofs' }),
    ).toBeTruthy();
  });

  test('falls back to the target key, or nothing', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.MEDIA,
        target_key: 'frc604',
      }),
    );
    expect(screen.getByText('frc604', { selector: 'span' })).toBeTruthy();
    cleanup();

    const { container } = renderWith(
      suggestionOf({ target_model: SuggestionType.ROBOT }),
    );
    expect(container.querySelector('h3')?.textContent).toBe('');
  });
});

describe('SuggestionReviewCard match video', () => {
  const MATCH = {
    target_model: SuggestionType.MATCH,
    target_key: '2026casj_qm12',
    event: EVENT_REFERENCE,
    contents: { youtube_videos: ['abc123'] },
  };

  test('previews the video and links the match and event', () => {
    renderWith(suggestionOf(MATCH));

    expect(screen.getByTestId('youtube-embed').dataset.videoId).toBe('abc123');
    expect(
      screen.getByRole('link', { name: '2026casj_qm12' }).getAttribute('href'),
    ).toBe('/match/2026casj_qm12');
    expect(
      screen.getByRole('link', {
        name: '2026 Silicon Valley Regional (2026casj)',
      }),
    ).toBeTruthy();
    expect(
      screen.getByRole('link', { name: 'https://youtu.be/abc123' }),
    ).toBeTruthy();
  });

  test('shows the title with hours or minutes of duration', () => {
    renderWith(
      suggestionOf({
        ...MATCH,
        video_title: 'Silicon Valley Qual 12',
        video_duration_seconds: 754,
      }),
    );
    expect(fieldValue('Title')).toBe('Silicon Valley Qual 12 (12m34s)');
    cleanup();

    renderWith(
      suggestionOf({
        ...MATCH,
        video_title: 'Silicon Valley Qual 12 full stream',
        video_duration_seconds: 3725,
      }),
    );
    expect(fieldValue('Title')).toBe(
      'Silicon Valley Qual 12 full stream (1h02m)',
    );
    expect(screen.getByText(/Video is 62 minutes long/)).toBeTruthy();
  });

  test('shows a title without a duration', () => {
    renderWith(suggestionOf({ ...MATCH, video_title: 'Qual 12' }));

    expect(fieldValue('Title')).toBe('Qual 12');
  });

  test('warns about mismatched titles and official webcasts', () => {
    renderWith(
      suggestionOf({
        ...MATCH,
        video_title: 'My summer vlog',
        has_first_official_webcast: true,
        uses_official_webcast_unit: true,
      }),
    );

    expect(
      screen.getByText(
        "Title doesn't mention this match or event — verify it's the right video",
      ),
    ).toBeTruthy();
    expect(screen.getByText(/FIRST webcasted event/)).toBeTruthy();
    expect(screen.getByText(/Official Webcast Unit — video may/)).toBeTruthy();
  });

  test('omits the preview without a video', () => {
    renderWith(suggestionOf({ ...MATCH, target_key: undefined, contents: {} }));

    expect(screen.queryByTestId('youtube-embed')).toBeNull();
    expect(screen.queryByText('Video:')).toBeNull();
    expect(
      (
        screen.getByLabelText(
          'Target match key (edit to redirect the video)',
        ) as HTMLInputElement
      ).value,
    ).toBe('');
  });

  test('redirects the video to another match', () => {
    const { onOverridesChange } = renderWith(suggestionOf(MATCH), {
      overrides: { year: 2026 },
    });
    const input = screen.getByLabelText(
      'Target match key (edit to redirect the video)',
    ) as HTMLInputElement;
    expect(input.value).toBe('2026casj_qm12');

    fireEvent.change(input, { target: { value: '2026casj_qm13' } });

    expect(onOverridesChange).toHaveBeenCalledWith({
      year: 2026,
      target_match_key: '2026casj_qm13',
    });
  });

  test('shows a redirect override', () => {
    renderWith(suggestionOf(MATCH), {
      overrides: { target_match_key: '2026casj_qm99' },
    });

    expect(
      (
        screen.getByLabelText(
          'Target match key (edit to redirect the video)',
        ) as HTMLInputElement
      ).value,
    ).toBe('2026casj_qm99');
  });
});

function mediaSuggestion(
  candidate_media: Record<string, unknown> | undefined,
  extra: Record<string, unknown> = {},
) {
  return suggestionOf({
    target_model: SuggestionType.MEDIA,
    reference: TEAM_REFERENCE,
    contents: { year: 2026 },
    candidate_media,
    ...extra,
  });
}

function stubImage({
  complete,
  width,
  height,
}: {
  complete: boolean;
  width: number;
  height: number;
}) {
  vi.spyOn(HTMLImageElement.prototype, 'complete', 'get').mockReturnValue(
    complete,
  );
  vi.spyOn(HTMLImageElement.prototype, 'naturalWidth', 'get').mockReturnValue(
    width,
  );
  vi.spyOn(HTMLImageElement.prototype, 'naturalHeight', 'get').mockReturnValue(
    height,
  );
}

const IMGUR = {
  slug_name: 'imgur',
  is_image: true,
  type_name: 'Imgur Image',
  image_direct_url: 'https://i.imgur.com/abc.png',
  external_link: 'https://imgur.com/abc',
};

describe('SuggestionReviewCard media previews', () => {
  test('shows nothing without candidate media', () => {
    renderWith(mediaSuggestion(undefined));

    expect(fieldValue('Type')).toBe('media');
    expect(screen.queryByRole('img')).toBeNull();
  });

  test('embeds Instagram posts', () => {
    renderWith(
      mediaSuggestion({
        slug_name: 'instagram-image',
        external_link: 'https://instagram.com/p/xyz',
      }),
    );

    expect(screen.getByTestId('instagram-embed').textContent).toBe(
      'https://instagram.com/p/xyz',
    );
  });

  test('skips Instagram posts without a link', () => {
    renderWith(mediaSuggestion({ slug_name: 'instagram-image' }));

    expect(screen.queryByTestId('instagram-embed')).toBeNull();
  });

  test('shows a direct image, or the thumbnail fallback', () => {
    renderWith(
      mediaSuggestion({
        slug_name: 'cdphotothread',
        is_image: true,
        image_direct_url: 'https://example.com/direct.jpg',
      }),
    );
    expect(
      screen.getByAltText('Suggested media preview').getAttribute('src'),
    ).toBe('https://example.com/direct.jpg');
    cleanup();

    renderWith(
      mediaSuggestion(
        { slug_name: 'cdphotothread', is_image: true },
        { details: { thumbnail: 'https://example.com/thumb.jpg' } },
      ),
    );
    expect(
      screen.getByAltText('Suggested media preview').getAttribute('src'),
    ).toBe('https://example.com/thumb.jpg');
  });

  test('shows no image without any URL', () => {
    renderWith(
      mediaSuggestion(
        { slug_name: 'cdphotothread', is_image: true },
        { details: { thumbnail: 42 } },
      ),
    );

    expect(screen.queryByAltText('Suggested media preview')).toBeNull();
  });

  test('embeds YouTube videos and links everything else', () => {
    renderWith(
      mediaSuggestion({ slug_name: 'youtube', foreign_key: 'vid123' }),
    );
    expect(screen.getByTestId('youtube-embed').dataset.videoId).toBe('vid123');
    cleanup();

    renderWith(
      mediaSuggestion({
        slug_name: 'grabcad',
        type_name: 'GrabCAD',
        external_link: 'https://grabcad.com/x',
      }),
    );
    expect(
      screen.getAllByRole('link', { name: 'https://grabcad.com/x' }),
    ).toHaveLength(2);
    expect(fieldValue('Type')).toBe('GrabCAD (https://grabcad.com/x)');
    cleanup();

    renderWith(mediaSuggestion({ slug_name: 'youtube' }));
    expect(screen.queryByTestId('youtube-embed')).toBeNull();
  });

  test('pre-selects reject when an already-loaded Imgur image was removed', () => {
    stubImage({ complete: true, width: 161, height: 81 });

    const { onDecisionChange } = renderWith(mediaSuggestion(IMGUR));

    expect(onDecisionChange).toHaveBeenCalledWith('reject');
    expect(
      screen.getByText('Image no longer exists on Imgur — Reject pre-selected'),
    ).toBeTruthy();
    expect(
      screen.getAllByRole('link', { name: IMGUR.external_link }),
    ).toHaveLength(2);
  });

  test('keeps a loaded Imgur image that still exists', () => {
    stubImage({ complete: true, width: 640, height: 480 });

    const { onDecisionChange } = renderWith(mediaSuggestion(IMGUR));

    expect(onDecisionChange).not.toHaveBeenCalled();
    expect(screen.getByAltText('Suggested media preview')).toBeTruthy();
  });

  test('checks an Imgur image when it finishes loading', () => {
    stubImage({ complete: false, width: 161, height: 81 });
    const { onDecisionChange } = renderWith(
      mediaSuggestion({ ...IMGUR, external_link: undefined }),
      { decision: 'accept' },
    );

    fireEvent.load(screen.getByAltText('Suggested media preview'));

    // A moderator's existing decision is left alone.
    expect(onDecisionChange).not.toHaveBeenCalled();
    expect(
      screen.getByText('Image no longer exists on Imgur — Reject pre-selected'),
    ).toBeTruthy();
    expect(screen.queryByRole('link', { name: /imgur\.com/ })).toBeNull();
  });

  test('treats an Imgur load error as removed', () => {
    stubImage({ complete: false, width: 0, height: 0 });
    const { onDecisionChange } = renderWith(mediaSuggestion(IMGUR));

    fireEvent.error(screen.getByAltText('Suggested media preview'));

    expect(onDecisionChange).toHaveBeenCalledWith('reject');
  });

  test('stops listening to an Imgur image after unmount', () => {
    stubImage({ complete: false, width: 161, height: 81 });
    const { onDecisionChange, unmount } = renderWith(mediaSuggestion(IMGUR));
    const image = screen.getByAltText('Suggested media preview');
    const remove = vi.spyOn(image, 'removeEventListener');

    unmount();

    expect(remove).toHaveBeenCalledWith('load', expect.any(Function));
    expect(remove).toHaveBeenCalledWith('error', expect.any(Function));
    expect(onDecisionChange).not.toHaveBeenCalled();
  });
});

describe('SuggestionReviewCard SmugMug albums', () => {
  function album(fields: Record<string, unknown>) {
    return suggestionOf({
      target_model: SuggestionType.EVENT_MEDIA,
      event: EVENT_REFERENCE,
      candidate_media: {
        slug_name: 'smugmug-album',
        external_link: 'https://smugmug.com/album',
        ...fields,
      },
    });
  }

  test('shows preview photos with a caption', () => {
    renderWith(
      album({
        title: 'Day 1',
        image_count: 1234,
        preview_images: [
          { image_url: 'https://img/1.jpg', web_uri: 'https://sm/1' },
          { image_url: 'https://img/2.jpg' },
          { web_uri: 'https://sm/skip' },
        ],
      }),
    );

    const photos = within(
      screen.getByTestId('smugmug-album-previews'),
    ).getAllByRole('link');
    expect(photos.map((photo) => photo.getAttribute('aria-label'))).toEqual([
      'Photo 1 of Day 1',
      'Photo 2 of Day 1',
    ]);
    expect(photos.map((photo) => photo.getAttribute('href'))).toEqual([
      'https://sm/1',
      'https://smugmug.com/album',
    ]);
    expect(
      screen.getByText(`Day 1 · ${(1234).toLocaleString()} photos`),
    ).toBeTruthy();
  });

  test('labels untitled photos and a single-photo album', () => {
    renderWith(
      album({
        image_count: 1,
        preview_images: [{ image_url: 'https://img/1.jpg' }],
      }),
    );

    expect(screen.getByRole('link', { name: 'Photo 1' })).toBeTruthy();
    expect(screen.getByText('1 photo')).toBeTruthy();
  });

  test('falls back to the cover image', () => {
    renderWith(album({ image_direct_url: 'https://img/cover.jpg' }));

    expect(screen.getByAltText('SmugMug album cover')).toBeTruthy();
    expect(screen.queryByTestId('smugmug-album-previews')).toBeNull();
    cleanup();

    renderWith(
      album({ image_direct_url: 'https://img/cover.jpg', title: 'Finals' }),
    );
    expect(screen.getByAltText('Finals')).toBeTruthy();
    expect(screen.getByText('Finals')).toBeTruthy();
  });

  test('shows nothing without photos, cover, or caption', () => {
    renderWith(album({}));

    expect(screen.queryByRole('img')).toBeNull();
    expect(fieldValue('Link')).toBe('https://smugmug.com/album');
  });
});

describe('SuggestionReviewCard team media', () => {
  const IMAGE = { slug_name: 'imgur', is_image: true, type_name: 'Imgur' };

  test('edits the year', () => {
    const { onOverridesChange } = renderWith(mediaSuggestion(IMAGE), {
      overrides: { set_preferred: false },
    });
    const year = screen.getByLabelText('Year') as HTMLInputElement;
    expect(year.value).toBe('2026');

    fireEvent.change(year, { target: { value: '2025' } });
    fireEvent.change(year, { target: { value: '' } });

    expect(onOverridesChange.mock.calls).toEqual([
      [{ set_preferred: false, year: 2025 }],
      [{ set_preferred: false, year: undefined }],
    ]);
  });

  test('shows a year override', () => {
    renderWith(mediaSuggestion(IMAGE), { overrides: { year: 2019 } });

    expect((screen.getByLabelText('Year') as HTMLInputElement).value).toBe(
      '2019',
    );
  });

  test('defaults "preferred" on when the team has none, and toggles it', () => {
    const { onOverridesChange } = renderWith(mediaSuggestion(IMAGE));
    const checkbox = screen.getByRole('checkbox', {
      name: 'Add as (p)referred team image',
    });
    expect(checkbox.getAttribute('aria-checked')).toBe('true');

    fireEvent.click(checkbox);

    expect(onOverridesChange).toHaveBeenCalledWith({ set_preferred: false });
  });

  test('lists existing preferred images below the cap', () => {
    const { onOverridesChange } = renderWith(
      mediaSuggestion(IMAGE, {
        existing_preferred: [
          {
            key: 'm1',
            foreign_key: 'abc',
            image_direct_url: 'https://i/1.png',
          },
        ],
      }),
      { overrides: { set_preferred: true } },
    );

    expect(
      screen.getByText(/Existing preferred images\s+\(1\/3\):/),
    ).toBeTruthy();
    expect(screen.getByAltText('abc')).toBeTruthy();
    const checkbox = screen.getByRole('checkbox', {
      name: 'Add as (p)referred team image',
    });
    expect(checkbox.getAttribute('aria-checked')).toBe('true');
    fireEvent.click(checkbox);
    expect(onOverridesChange).toHaveBeenCalledWith({ set_preferred: false });
    expect(screen.queryByRole('radio')).toBeNull();
  });

  test('offers to replace a preferred image at the cap', () => {
    const { onOverridesChange } = renderWith(
      mediaSuggestion(IMAGE, {
        max_preferred: 2,
        existing_preferred: [
          { key: 'm1', image_direct_url: 'https://i/1.png' },
          { key: 'm2' },
        ],
      }),
      { overrides: { replace_preferred_media_key: 'm2' } },
    );

    expect(
      screen.getByText(/already has 2 preferred\s+images \(max 2\)/),
    ).toBeTruthy();
    expect(screen.queryByRole('checkbox')).toBeNull();
    expect(screen.getByAltText('existing preferred')).toBeTruthy();
    const radios = screen.getAllByRole('radio') as HTMLInputElement[];
    expect(radios.map((radio) => radio.checked)).toEqual([false, true, false]);

    fireEvent.click(radios[0]);
    fireEvent.click(screen.getByRole('radio', { name: 'Keep current' }));

    expect(onOverridesChange.mock.calls).toEqual([
      [{ replace_preferred_media_key: 'm1' }],
      [{ replace_preferred_media_key: undefined }],
    ]);
  });

  test('shows existing preferred images without controls for non-images', () => {
    renderWith(
      mediaSuggestion(
        { slug_name: 'youtube', foreign_key: 'vid' },
        { max_preferred: 1, existing_preferred: [{ key: 'm1' }] },
      ),
    );

    expect(screen.getByText(/already has 1 preferred/)).toBeTruthy();
    expect(screen.queryByRole('radio')).toBeNull();
    expect(screen.queryByRole('checkbox')).toBeNull();
  });
});

describe('SuggestionReviewCard social media', () => {
  function social(
    slug: string,
    contents: Record<string, unknown>,
    media: Record<string, unknown> = {},
  ) {
    return suggestionOf({
      target_model: SuggestionType.SOCIAL_MEDIA,
      reference: TEAM_REFERENCE,
      contents,
      candidate_media: { slug_name: slug, type_name: 'Profile', ...media },
    });
  }

  test('embeds a Facebook page', () => {
    renderWith(
      social('facebook-profile', {
        site_name: 'Facebook',
        foreign_key: 'team254',
        profile_url: 'https://facebook.com/team254',
      }),
    );

    expect(screen.getByTitle('Facebook page team254').getAttribute('src')).toBe(
      'https://www.facebook.com/plugins/page.php?href=https%3A%2F%2Fwww.facebook.com%2Fteam254&width=340&tabs=',
    );
    expect(fieldValue('Site')).toBe('Facebook');
    expect(fieldValue('Profile')).toBe('https://facebook.com/team254');
  });

  test('shows a GitHub profile card', () => {
    renderWith(
      social(
        'github-profile',
        { foreign_key: 'team254' },
        { social_profile_url: 'https://github.com/team254' },
      ),
    );

    expect(
      screen.getByAltText('team254 avatar').closest('a')?.getAttribute('href'),
    ).toBe('https://github.com/team254');
    expect(fieldValue('Site')).toBe('Profile');
  });

  test('builds the GitHub link when there is no profile URL', () => {
    renderWith(social('github-profile', { foreign_key: 'team254' }));

    expect(
      screen.getByAltText('team254 avatar').closest('a')?.getAttribute('href'),
    ).toBe('https://github.com/team254');
    expect(screen.queryByText('Profile:')).toBeNull();
  });

  test('shows other profiles without an embed', () => {
    renderWith(social('instagram-profile', { foreign_key: 'team254' }));

    expect(screen.queryByRole('img')).toBeNull();
    expect(screen.queryByTitle(/Facebook page/)).toBeNull();
  });

  test('pre-selects reject once for a malformed submission', () => {
    const suggestion = social('facebook-profile', {
      foreign_key: 'profile.php?id=1',
    });
    const { onDecisionChange, rerender } = renderWith(suggestion);

    expect(onDecisionChange).toHaveBeenCalledTimes(1);
    expect(onDecisionChange).toHaveBeenCalledWith('reject');
    expect(
      screen.getByText(/personal profile link.*Reject pre-selected/),
    ).toBeTruthy();
    expect(screen.queryByTitle(/Facebook page/)).toBeNull();

    // Clearing the decision afterwards sticks.
    rerender(
      <SuggestionReviewCard
        suggestion={suggestion}
        decision={undefined}
        onDecisionChange={onDecisionChange}
        overrides={{ year: 2026 }}
        onOverridesChange={() => {}}
      />,
    );
    expect(onDecisionChange).toHaveBeenCalledTimes(1);
  });

  test('leaves an existing decision on a malformed submission', () => {
    const { onDecisionChange } = renderWith(
      social('github-profile', { foreign_key: 'https://github.com/x' }),
      { decision: 'accept' },
    );

    expect(onDecisionChange).not.toHaveBeenCalled();
  });
});

describe('SuggestionReviewCard robot CAD', () => {
  test('shows the model preview and details', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.ROBOT,
        reference: TEAM_REFERENCE,
        details: {
          model_image: 'https://cad/model.png',
          model_name: 'Robot 2026',
          model_description: 'Full robot',
        },
        candidate_media: { external_link: 'https://cad/model' },
      }),
    );

    expect(screen.getByAltText('Robot 2026')).toBeTruthy();
    expect(fieldValue('Model')).toBe('Robot 2026');
    expect(fieldValue('Description')).toBe('Full robot');
    expect(fieldValue('Link')).toBe('https://cad/model');
  });

  test('labels an unnamed model preview', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.ROBOT,
        details: { model_image: 'https://cad/model.png', model_name: 7 },
      }),
    );

    expect(screen.getByAltText('CAD model preview')).toBeTruthy();
    expect(screen.queryByText('Model:')).toBeNull();
  });
});

describe('SuggestionReviewCard event media', () => {
  test('previews the media and links the event', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.EVENT_MEDIA,
        event: EVENT_REFERENCE,
        candidate_media: { slug_name: 'youtube', foreign_key: 'vid' },
      }),
    );

    expect(screen.getByTestId('youtube-embed')).toBeTruthy();
    expect(fieldValue('Event')).toBe('2026 Silicon Valley Regional (2026casj)');
    expect(screen.queryByText('Link:')).toBeNull();
  });
});

describe('SuggestionReviewCard webcast', () => {
  const WEBCAST = {
    target_model: SuggestionType.EVENT,
    event: {
      ...EVENT_REFERENCE,
      start_date: '2026-03-05',
      end_date: '2026-03-07',
    },
    contents: {
      webcast_url: 'https://twitch.tv/firstinspires',
      webcast_dict: { type: 'twitch', channel: 'firstinspires', file: 'f1' },
      webcast_date: '2026-03-06',
    },
    existing_webcasts: [
      { type: 'youtube', channel: 'abc' },
      { type: 'twitch', channel: 'x', file: 'y' },
    ],
    uses_official_webcast_unit: true,
  };

  test('shows the event, existing webcasts, and the suggestion', () => {
    renderWith(suggestionOf(WEBCAST));

    expect(fieldValue('Event')).toBe(
      `2026 Silicon Valley Regional (2026casj) (${formatEventDateRange('2026-03-05', '2026-03-07')})`,
    );
    expect(fieldValue('Existing webcasts')).toBe(
      'youtube / abc, twitch / x / y',
    );
    expect(fieldValue('Suggested URL')).toBe('https://twitch.tv/firstinspires');
    expect(
      screen.getByText('District uses the Official Webcast Unit'),
    ).toBeTruthy();
  });

  test('says when there are no webcasts yet', () => {
    renderWith(
      suggestionOf({
        target_model: SuggestionType.EVENT,
        event: EVENT_REFERENCE,
        contents: {},
      }),
    );

    expect(fieldValue('Event')).toBe('2026 Silicon Valley Regional (2026casj)');
    expect(fieldValue('Existing webcasts')).toBe('None yet!');
    expect(screen.queryByText('Suggested URL:')).toBeNull();
    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe('');
    expect((screen.getByLabelText('Channel') as HTMLInputElement).value).toBe(
      '',
    );
  });

  test('hides event context when grouped under an event', () => {
    renderWith(suggestionOf(WEBCAST), { hideEventContext: true });

    expect(screen.queryByText('Event:')).toBeNull();
    expect(screen.queryByText('Existing webcasts:')).toBeNull();
  });

  test('prefills and edits the webcast fields', () => {
    const { onOverridesChange } = renderWith(suggestionOf(WEBCAST));

    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe(
      'twitch',
    );
    expect((screen.getByLabelText('Channel') as HTMLInputElement).value).toBe(
      'firstinspires',
    );
    expect(
      (screen.getByLabelText('File (optional)') as HTMLInputElement).value,
    ).toBe('f1');
    expect(
      (screen.getByLabelText('Date (optional)') as HTMLInputElement).value,
    ).toBe('2026-03-06');

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'youtube' },
    });
    fireEvent.change(screen.getByLabelText('Channel'), {
      target: { value: 'c2' },
    });
    fireEvent.change(screen.getByLabelText('File (optional)'), {
      target: { value: 'f2' },
    });
    fireEvent.change(screen.getByLabelText('Date (optional)'), {
      target: { value: '2026-03-07' },
    });

    expect(onOverridesChange.mock.calls).toEqual([
      [{ webcast_type: 'youtube' }],
      [{ webcast_channel: 'c2' }],
      [{ webcast_file: 'f2' }],
      [{ webcast_date: '2026-03-07' }],
    ]);
  });

  test('shows moderator overrides', () => {
    renderWith(suggestionOf(WEBCAST), {
      overrides: {
        webcast_type: 'html5',
        webcast_channel: 'c3',
        webcast_file: 'f3',
        webcast_date: '2026-03-08',
      },
    });

    expect((screen.getByRole('combobox') as HTMLSelectElement).value).toBe(
      'html5',
    );
    expect((screen.getByLabelText('Channel') as HTMLInputElement).value).toBe(
      'c3',
    );
    expect(
      (screen.getByLabelText('File (optional)') as HTMLInputElement).value,
    ).toBe('f3');
    expect(
      (screen.getByLabelText('Date (optional)') as HTMLInputElement).value,
    ).toBe('2026-03-08');
  });
});

describe('SuggestionReviewCard offseason event fields', () => {
  test('lists similar events from this year and last', () => {
    renderWith(
      suggestionOf({
        ...OFFSEASON_SUGGESTION,
        similar_events: [{ key: '2026cc', name: 'Chezy Champs' }],
        similar_events_last_year: [{ key: '2025cc', name: 'Old Champs' }],
      }),
    );

    expect(screen.getByText('Similar events this year:')).toBeTruthy();
    expect(
      screen
        .getByRole('link', { name: 'Chezy Champs (2026cc)' })
        .getAttribute('href'),
    ).toBe('/event/2026cc');
    expect(screen.getByText('Similar events last year:')).toBeTruthy();
    expect(screen.getByRole('link', { name: /Old Champs/ })).toBeTruthy();
  });

  test('edits every field', () => {
    const { onOverridesChange } = renderWith(OFFSEASON_SUGGESTION);
    const edits: [string, keyof AcceptRequest][] = [
      ["Event short (required, e.g. 'cc')", 'event_short'],
      ['Name', 'name'],
      ['Short name', 'short_name'],
      ['Start date', 'start_date'],
      ['End date', 'end_date'],
      ['Website', 'website'],
      ['Venue', 'venue'],
      ['Address', 'venue_address'],
      ['City', 'city'],
      ['State', 'state'],
      ['Country', 'country'],
      ['FIRST code (official events only)', 'first_code'],
    ];

    for (const [label] of edits) {
      fireEvent.change(screen.getByLabelText(label), {
        target: { value: `new ${label}` },
      });
    }

    expect(onOverridesChange.mock.calls).toEqual(
      edits.map(([label, key]) => [{ [key]: `new ${label}` }]),
    );
  });

  test('prefills fields from the suggestion and shows overrides', () => {
    renderWith(OFFSEASON_SUGGESTION, {
      overrides: { name: 'Chezy Champs 2026', short_name: 'Chezy' },
    });

    expect((screen.getByLabelText('Name') as HTMLInputElement).value).toBe(
      'Chezy Champs 2026',
    );
    expect(
      (screen.getByLabelText('Short name') as HTMLInputElement).value,
    ).toBe('Chezy');
    expect((screen.getByLabelText('Venue') as HTMLInputElement).value).toBe(
      'Bellarmine College Preparatory',
    );
    expect((screen.getByLabelText('Address') as HTMLInputElement).value).toBe(
      '960 W Hedding St',
    );
    expect(screen.queryByText('FIRST page preview:')).toBeNull();
  });

  test('previews the FIRST page for the event short in the start year', () => {
    renderWith(OFFSEASON_SUGGESTION, { overrides: { event_short: 'cc' } });

    expect(
      screen
        .getByRole('link', { name: 'frc-events.firstinspires.org/2026/CC' })
        .getAttribute('href'),
    ).toBe('https://frc-events.firstinspires.org/2026/CC');
  });

  test('prefers the FIRST code and falls back to the current year', () => {
    renderWith(
      suggestionOf({
        ...OFFSEASON_SUGGESTION,
        contents: { first_code: 'casj', start_date: 'soon' },
      }),
    );

    const year = Temporal.Now.plainDateISO().year;
    expect(
      screen.getByRole('link', {
        name: `frc-events.firstinspires.org/${year}/CASJ`,
      }),
    ).toBeTruthy();
  });
});

describe('SuggestionReviewCard api write details', () => {
  function apiWrite(fields: Record<string, unknown>) {
    return suggestionOf({ ...API_WRITE_SUGGESTION, ...fields });
  }

  function eventOn(start: Temporal.PlainDate, end: Temporal.PlainDate) {
    return {
      ...API_WRITE_SUGGESTION.event,
      start_date: start.toString(),
      end_date: end.toString(),
    };
  }

  test('badges ongoing and past events', () => {
    const today = Temporal.Now.plainDateISO();
    renderWith(
      apiWrite({
        event: eventOn(today.subtract({ days: 1 }), today.add({ days: 1 })),
      }),
    );
    expect(screen.getByText('Happening now')).toBeTruthy();
    cleanup();

    renderWith(
      apiWrite({
        event: eventOn(
          today.subtract({ days: 9 }),
          today.subtract({ days: 7 }),
        ),
      }),
    );
    expect(screen.getByText('Ended 7 days ago')).toBeTruthy();
  });

  test('shows the requester, affiliation, and existing keys', () => {
    renderWith(
      apiWrite({
        author: { nickname: 'Scout', email: 'scout@example.com' },
        existing_auth: [
          {
            owner_email: 'owner@example.com',
            auth_types: [{ type: 3, name: 'event matches' }],
          },
          {},
        ],
      }),
    );

    expect(fieldValue('User')).toBe('Scout (scout@example.com)');
    expect(fieldValue('Affiliation')).toBe('Team 254');
    expect(
      screen.getByText('Existing keys already granted for this event:'),
    ).toBeTruthy();
    const items = screen.getAllByRole('listitem').map((li) => li.textContent);
    expect(items).toEqual([
      'owner@example.com (event matches)',
      'unknown owner ()',
    ]);
  });

  test('shows an unknown requester', () => {
    renderWith(apiWrite({ author: undefined }));

    expect(fieldValue('User')).toBe('unknown');
    expect(screen.queryByRole('list')).toBeNull();
  });

  test('pre-checks requested auth types and toggles them', () => {
    const { onOverridesChange } = renderWith(
      apiWrite({
        requested_auth_types: [
          { type: 3, name: 'event matches' },
          { name: 'typeless' },
        ],
      }),
    );

    expect(
      screen
        .getByRole('checkbox', { name: 'event matches' })
        .getAttribute('aria-checked'),
    ).toBe('true');
    expect(
      screen
        .getByRole('checkbox', { name: 'event teams' })
        .getAttribute('aria-checked'),
    ).toBe('false');

    fireEvent.click(screen.getByRole('checkbox', { name: 'event teams' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'event matches' }));

    expect(onOverridesChange.mock.calls).toEqual([
      [{ auth_types: [3, 2] }],
      [{ auth_types: [] }],
    ]);
  });

  test('uses overridden auth types and treats missing requests as none', () => {
    renderWith(apiWrite({ requested_auth_types: undefined }), {
      overrides: { auth_types: [7] },
    });

    expect(
      screen
        .getByRole('checkbox', { name: 'event info' })
        .getAttribute('aria-checked'),
    ).toBe('true');
    expect(
      screen
        .getByRole('checkbox', { name: 'event matches' })
        .getAttribute('aria-checked'),
    ).toBe('false');
  });

  test('sets the expiration and the requester message', () => {
    const { onOverridesChange } = renderWith(apiWrite({}), {
      overrides: { expiration_days: 30 },
    });
    const expiration = screen.getByDisplayValue('30 days');

    fireEvent.change(expiration, { target: { value: '-1' } });
    fireEvent.change(
      screen.getByRole('textbox', { name: /Message for the requester/ }),
      {
        target: { value: 'Have fun!' },
      },
    );

    expect(onOverridesChange.mock.calls).toEqual([
      [{ expiration_days: -1 }],
      [{ expiration_days: 30, user_message: 'Have fun!' }],
    ]);
  });

  test('defaults the expiration to a week', () => {
    renderWith(apiWrite({}));

    expect(screen.getByDisplayValue('7 days')).toBeTruthy();
  });
});
