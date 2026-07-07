import { Link } from '@tanstack/react-router';
import { type JSX, useEffect, useRef, useState } from 'react';
import { InstagramEmbed } from 'react-social-media-embed';
import { Temporal } from 'temporal-polyfill';

import type {
  AcceptRequest,
  ModerationSuggestion,
} from '~/api/tba/moderation/types.gen';
import { YoutubeEmbed } from '~/components/tba/videoEmbeds';
import { Badge } from '~/components/ui/badge';
import { Button } from '~/components/ui/button';
import { Card, CardHeader, CardTitle } from '~/components/ui/card';
import { Checkbox } from '~/components/ui/checkbox';
import { Input } from '~/components/ui/input';
import {
  defaultExpirationDays,
  defaultSetPreferred,
  formatAuthorReputation,
  formatEventDateRange,
  matchVideoDurationWarning,
  matchVideoTitleWarning,
  socialProfileWarning,
} from '~/lib/moderationUtils';
import { cn } from '~/lib/utils';

export type ReviewDecision = 'accept' | 'reject' | undefined;

interface SuggestionReviewCardProps {
  suggestion: ModerationSuggestion;
  decision: ReviewDecision;
  onDecisionChange: (decision: ReviewDecision) => void;
  overrides: AcceptRequest;
  onOverridesChange: (overrides: AcceptRequest) => void;
  /** Skip per-card event context when cards are grouped under an event. */
  hideEventContext?: boolean;
  /** Highlight this card as the keyboard-navigation target. */
  focused?: boolean;
}

// The write auth types moderators can grant for api_auth_access suggestions,
// mirroring AuthType / WRITE_TYPE_NAMES on the backend
const WRITE_AUTH_TYPES: { type: number; name: string }[] = [
  { type: 1, name: 'match video' },
  { type: 2, name: 'event teams' },
  { type: 3, name: 'event matches' },
  { type: 4, name: 'event rankings' },
  { type: 5, name: 'event alliances' },
  { type: 6, name: 'event awards' },
  { type: 7, name: 'event info' },
  { type: 8, name: 'zebra motionworks' },
];

const WEBCAST_TYPES = [
  'twitch',
  'youtube',
  'iframe',
  'mms',
  'rtmp',
  'ustream',
  'livestream',
  'html5',
  'dacast',
  'stemtv',
];

function contentsString(suggestion: ModerationSuggestion, key: string): string {
  const value = suggestion.contents[key];
  return typeof value === 'string' || typeof value === 'number'
    ? String(value)
    : '';
}

function ExternalLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="break-all text-primary underline underline-offset-2"
    >
      {children}
    </a>
  );
}

function ReferenceLink({
  suggestion,
}: {
  suggestion: ModerationSuggestion;
}): JSX.Element | null {
  const reference = suggestion.reference ?? suggestion.event;
  if (!reference) {
    return suggestion.target_key ? <span>{suggestion.target_key}</span> : null;
  }
  if (reference.type === 'team') {
    // Link into the suggestion's year when it has one, like the web review UI
    const year = contentsString(suggestion, 'year');
    return (
      <Link
        to="/team/$teamNumber/{-$year}"
        params={{
          teamNumber: String(reference.team_number ?? ''),
          year: year || undefined,
        }}
        className="text-primary underline underline-offset-2"
      >
        Team {reference.team_number} - {reference.nickname}
        {year ? ` (${year})` : ''}
      </Link>
    );
  }
  return (
    <Link
      to="/event/$eventKey"
      params={{ eventKey: reference.key }}
      className="text-primary underline underline-offset-2"
    >
      {reference.year} {reference.name} ({reference.key})
    </Link>
  );
}

// Two-column card body on desktop, like the web review UI's dense layout:
// media preview on one side, fields and controls on the other. Stacks on
// mobile. previewSide="right" keeps previews flush with the card's right
// edge so a moderator can scan straight down the right column.
function PreviewLayout({
  preview,
  previewSide = 'left',
  children,
}: {
  preview: React.ReactNode;
  previewSide?: 'left' | 'right';
  children: React.ReactNode;
}): JSX.Element {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:gap-6">
      <div
        className={cn(
          'min-w-0 lg:w-2/5 lg:shrink-0',
          previewSide === 'right' && 'lg:order-last lg:flex lg:justify-end',
        )}
      >
        {preview}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-3">{children}</div>
    </div>
  );
}

function FieldRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="font-medium text-muted-foreground">{label}:</span>
      <span>{children}</span>
    </div>
  );
}

function LabeledInput({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}): JSX.Element {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="font-medium text-muted-foreground">{label}</span>
      <Input
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

// Amber advisory badge: something to verify before accepting, softer than
// the destructive red used for near-certain problems
function WarningBadge({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  return (
    <Badge
      variant="outline"
      className="w-fit border-amber-500/60 bg-amber-500/15 text-amber-700
        dark:text-amber-400"
    >
      {children}
    </Badge>
  );
}

function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return hours > 0
    ? `${hours}h${String(minutes).padStart(2, '0')}m`
    : `${minutes}m${String(seconds).padStart(2, '0')}s`;
}

function MatchVideoDetails({
  suggestion,
  overrides,
  onOverridesChange,
}: SuggestionReviewCardProps): JSX.Element {
  const videos = suggestion.contents.youtube_videos;
  const videoId =
    Array.isArray(videos) && typeof videos[0] === 'string' ? videos[0] : '';
  const titleWarning = matchVideoTitleWarning(
    suggestion.video_title,
    suggestion.target_key,
    suggestion.event,
  );
  const durationWarning = matchVideoDurationWarning(
    suggestion.video_duration_seconds,
    videoId,
  );
  return (
    <PreviewLayout
      preview={
        videoId && (
          <YoutubeEmbed
            videoId={videoId}
            title={`Suggested video for ${suggestion.target_key}`}
          />
        )
      }
    >
      <FieldRow label="Match">
        <Link
          to="/match/$matchKey"
          params={{ matchKey: suggestion.target_key ?? '' }}
          className="text-primary underline underline-offset-2"
        >
          {suggestion.target_key}
        </Link>
      </FieldRow>
      <FieldRow label="Event">
        <ReferenceLink suggestion={suggestion} />
      </FieldRow>
      {videoId && (
        <FieldRow label="Video">
          <ExternalLink href={`https://youtu.be/${videoId}`}>
            https://youtu.be/{videoId}
          </ExternalLink>
        </FieldRow>
      )}
      {suggestion.video_title && (
        <FieldRow label="Title">
          {suggestion.video_title}
          {suggestion.video_duration_seconds
            ? ` (${formatDuration(suggestion.video_duration_seconds)})`
            : ''}
        </FieldRow>
      )}
      {titleWarning && <WarningBadge>{titleWarning}</WarningBadge>}
      {durationWarning && <WarningBadge>{durationWarning}</WarningBadge>}
      {suggestion.has_first_official_webcast && (
        <Badge variant="destructive" className="w-fit">
          FIRST webcasted event — please ensure this isn&apos;t a stream-ripped
          video
        </Badge>
      )}
      {suggestion.uses_official_webcast_unit && (
        <Badge variant="destructive" className="w-fit">
          Official Webcast Unit — video may already be uploaded by FIRST
        </Badge>
      )}
      <div className="max-w-xs">
        <LabeledInput
          label="Target match key (edit to redirect the video)"
          value={overrides.target_match_key ?? suggestion.target_key ?? ''}
          onChange={(value) =>
            onOverridesChange({ ...overrides, target_match_key: value })
          }
        />
      </div>
    </PreviewLayout>
  );
}

function MediaPreview({
  suggestion,
  onUnavailable,
}: {
  suggestion: ModerationSuggestion;
  onUnavailable?: () => void;
}): JSX.Element | null {
  const media = suggestion.candidate_media;
  const [imageRemoved, setImageRemoved] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const isImgur = media?.slug_name === 'imgur';

  useEffect(() => {
    // Imgur serves a 302 to /removed.png (161x81) for deleted images rather
    // than a 404 — same detection ImgurEmbed uses on team pages
    const img = imgRef.current;
    if (!img || !isImgur) return;
    const markRemoved = () => {
      setImageRemoved(true);
      onUnavailable?.();
    };
    const check = () => {
      if (img.naturalWidth === 161 && img.naturalHeight === 81) {
        markRemoved();
      }
    };
    if (img.complete) {
      check();
    } else {
      img.addEventListener('load', check);
      img.addEventListener('error', markRemoved);
      return () => {
        img.removeEventListener('load', check);
        img.removeEventListener('error', markRemoved);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isImgur]);

  if (!media) return null;
  // Instagram posts embed via the same widget the team media gallery uses
  if (media.slug_name === 'instagram-image') {
    return media.external_link ? (
      <div className="max-w-sm">
        <InstagramEmbed url={media.external_link} width="100%" />
      </div>
    ) : null;
  }
  if (media.is_image) {
    const imageUrl =
      media.image_direct_url ??
      (typeof suggestion.details?.thumbnail === 'string'
        ? suggestion.details.thumbnail
        : undefined);
    if (imageRemoved) {
      return (
        <div className="flex flex-col gap-2">
          <Badge variant="destructive" className="w-fit">
            Image no longer exists on Imgur — Reject pre-selected
          </Badge>
          {media.external_link && (
            <ExternalLink href={media.external_link}>
              {media.external_link}
            </ExternalLink>
          )}
        </div>
      );
    }
    return imageUrl ? (
      <img
        ref={imgRef}
        src={imageUrl}
        alt="Suggested media preview"
        className="max-h-80 w-fit max-w-full rounded-lg border"
      />
    ) : null;
  }
  if (media.slug_name === 'youtube' && media.foreign_key) {
    return (
      <YoutubeEmbed
        videoId={media.foreign_key}
        title="Suggested video"
        className="max-w-xl"
      />
    );
  }
  if (media.external_link) {
    return (
      <ExternalLink href={media.external_link}>
        {media.external_link}
      </ExternalLink>
    );
  }
  return null;
}

function TeamMediaDetails({
  suggestion,
  decision,
  onDecisionChange,
  overrides,
  onOverridesChange,
}: SuggestionReviewCardProps): JSX.Element {
  const isImage = suggestion.candidate_media?.is_image ?? false;
  const existingPreferred = suggestion.existing_preferred ?? [];
  const maxPreferred = suggestion.max_preferred ?? 3;
  const atCap = existingPreferred.length >= maxPreferred;
  return (
    <div className="flex flex-col gap-3">
      <PreviewLayout
        preview={
          <MediaPreview
            suggestion={suggestion}
            onUnavailable={() => {
              // Dead image: pre-select reject unless the moderator already
              // made a call
              if (decision === undefined) onDecisionChange('reject');
            }}
          />
        }
      >
        <FieldRow label="Type">
          {suggestion.candidate_media?.type_name ?? suggestion.target_model}
          {suggestion.candidate_media?.external_link && (
            <>
              {' ('}
              <ExternalLink href={suggestion.candidate_media.external_link}>
                {suggestion.candidate_media.external_link}
              </ExternalLink>
              {')'}
            </>
          )}
        </FieldRow>
        <div className="flex items-center gap-2 text-sm">
          <label
            htmlFor={`year-${suggestion.key}`}
            className="font-medium text-muted-foreground"
          >
            Year
          </label>
          <Input
            id={`year-${suggestion.key}`}
            className="w-24"
            value={String(overrides.year ?? contentsString(suggestion, 'year'))}
            onChange={(e) =>
              onOverridesChange({
                ...overrides,
                year: e.target.value ? Number(e.target.value) : undefined,
              })
            }
          />
        </div>
        {isImage && !atCap && (
          <div className="flex items-center gap-2 text-sm">
            <Checkbox
              id={`preferred-${suggestion.key}`}
              checked={
                overrides.set_preferred ?? defaultSetPreferred(suggestion)
              }
              onCheckedChange={(checked) =>
                onOverridesChange({
                  ...overrides,
                  set_preferred: checked === true,
                })
              }
            />
            <label htmlFor={`preferred-${suggestion.key}`}>
              Add as (p)referred team image
            </label>
          </div>
        )}
        {existingPreferred.length > 0 && (
          <div className="flex flex-col gap-2 text-sm">
            <span className="font-medium text-muted-foreground">
              {atCap
                ? `This team already has ${existingPreferred.length} preferred
                images (max ${maxPreferred}). Optionally choose one to
                replace:`
                : `Existing preferred images
                (${existingPreferred.length}/${maxPreferred}):`}
            </span>
            <div className="flex flex-wrap gap-3">
              {existingPreferred.map((media) => (
                <label
                  key={media.key}
                  className="flex flex-col items-center gap-1"
                >
                  {media.image_direct_url && (
                    <img
                      src={media.image_direct_url}
                      alt={media.foreign_key ?? 'existing preferred'}
                      className="max-h-24 rounded border"
                    />
                  )}
                  {isImage && atCap && (
                    <span className="flex items-center gap-1">
                      <input
                        type="radio"
                        name={`replace-${suggestion.key}`}
                        checked={
                          overrides.replace_preferred_media_key === media.key
                        }
                        onChange={() =>
                          onOverridesChange({
                            ...overrides,
                            replace_preferred_media_key: media.key,
                          })
                        }
                      />
                      Replace
                    </span>
                  )}
                </label>
              ))}
              {isImage && atCap && (
                <label className="flex items-center gap-1 self-center">
                  <input
                    type="radio"
                    name={`replace-${suggestion.key}`}
                    checked={!overrides.replace_preferred_media_key}
                    onChange={() =>
                      onOverridesChange({
                        ...overrides,
                        replace_preferred_media_key: undefined,
                      })
                    }
                  />
                  Keep current
                </label>
              )}
            </div>
          </div>
        )}
      </PreviewLayout>
    </div>
  );
}

function SocialMediaDetails({
  suggestion,
  decision,
  onDecisionChange,
}: SuggestionReviewCardProps): JSX.Element {
  // Prefer the URL as submitted; the candidate media's URL is re-derived
  // from a template and can differ from what the suggester actually sent
  const profileUrl =
    contentsString(suggestion, 'profile_url') ||
    suggestion.candidate_media?.social_profile_url ||
    '';
  const foreignKey = contentsString(suggestion, 'foreign_key');
  const slug = suggestion.candidate_media?.slug_name;
  // Malformed submissions (personal-profile/group links, video URLs) should
  // be caught before a moderator accepts them
  const warning = socialProfileWarning(slug, foreignKey);
  // Malformed submission: pre-select reject once, unless the moderator
  // already made a call. One-shot so deselecting reject sticks.
  const preselectedReject = useRef(false);
  useEffect(() => {
    if (warning && decision === undefined && !preselectedReject.current) {
      preselectedReject.current = true;
      onDecisionChange('reject');
    }
  }, [warning, decision, onDecisionChange]);
  // GitHub serves hotlinkable avatars, so it gets a profile card like the
  // web review UI's github-card embed
  const isGithub = slug === 'github-profile';
  const embed =
    slug === 'facebook-profile' && foreignKey && !warning ? (
      // The modern page plugin renders one fixed-height card (cover +
      // name + Follow, ~335px at width 340) regardless of the legacy
      // small_header/hide_cover params, so size the iframe to fit it
      <iframe
        src={`https://www.facebook.com/plugins/page.php?href=${encodeURIComponent(
          `https://www.facebook.com/${foreignKey}`,
        )}&width=340&tabs=`}
        width={340}
        height={345}
        loading="lazy"
        title={`Facebook page ${foreignKey}`}
        className="rounded-lg border"
      />
    ) : isGithub && foreignKey && !warning ? (
      <a
        href={profileUrl || `https://github.com/${foreignKey}`}
        target="_blank"
        rel="noreferrer"
        className="flex h-fit w-fit items-center gap-3 rounded-lg border p-3
          transition-colors hover:bg-accent"
      >
        <img
          src={`https://github.com/${foreignKey}.png?size=96`}
          alt={`${foreignKey} avatar`}
          className="size-12 rounded-full"
        />
        <div>
          <div className="font-medium">{foreignKey}</div>
          <div className="text-sm text-muted-foreground">
            github.com/{foreignKey}
          </div>
        </div>
      </a>
    ) : null;
  const fields = (
    <>
      <FieldRow label="Site">
        {contentsString(suggestion, 'site_name') ||
          suggestion.candidate_media?.type_name}
      </FieldRow>
      {warning && (
        <Badge variant="destructive" className="w-fit">
          {warning} — Reject pre-selected
        </Badge>
      )}
      {profileUrl && (
        <FieldRow label="Profile">
          <ExternalLink href={profileUrl}>{profileUrl}</ExternalLink>
        </FieldRow>
      )}
    </>
  );
  // Embeds go in a right-hand column so moderators can scan straight down
  // the previews; cards without an embed stay a plain stack
  return embed ? (
    <PreviewLayout preview={embed} previewSide="right">
      {fields}
    </PreviewLayout>
  ) : (
    <div className="flex flex-col gap-3">{fields}</div>
  );
}

function RobotCadDetails({
  suggestion,
}: SuggestionReviewCardProps): JSX.Element {
  const details = suggestion.details ?? {};
  const modelImage =
    typeof details.model_image === 'string' ? details.model_image : undefined;
  const modelName =
    typeof details.model_name === 'string' ? details.model_name : undefined;
  const modelDescription =
    typeof details.model_description === 'string'
      ? details.model_description
      : undefined;
  return (
    <PreviewLayout
      preview={
        modelImage && (
          <img
            src={modelImage}
            alt={modelName ?? 'CAD model preview'}
            className="max-h-80 w-full rounded-lg border object-contain"
          />
        )
      }
    >
      {modelName && <FieldRow label="Model">{modelName}</FieldRow>}
      {modelDescription && (
        <FieldRow label="Description">{modelDescription}</FieldRow>
      )}
      {suggestion.candidate_media?.external_link && (
        <FieldRow label="Link">
          <ExternalLink href={suggestion.candidate_media.external_link}>
            {suggestion.candidate_media.external_link}
          </ExternalLink>
        </FieldRow>
      )}
    </PreviewLayout>
  );
}

function EventMediaDetails({
  suggestion,
}: SuggestionReviewCardProps): JSX.Element {
  return (
    <PreviewLayout preview={<MediaPreview suggestion={suggestion} />}>
      <FieldRow label="Event">
        <ReferenceLink suggestion={suggestion} />
      </FieldRow>
      {suggestion.candidate_media?.external_link && (
        <FieldRow label="Link">
          <ExternalLink href={suggestion.candidate_media.external_link}>
            {suggestion.candidate_media.external_link}
          </ExternalLink>
        </FieldRow>
      )}
    </PreviewLayout>
  );
}

function WebcastDetails({
  suggestion,
  overrides,
  onOverridesChange,
  hideEventContext,
}: SuggestionReviewCardProps): JSX.Element {
  const webcastDict = suggestion.contents.webcast_dict as
    { type?: string; channel?: string; file?: string } | undefined;
  const webcastUrl = contentsString(suggestion, 'webcast_url');
  const existingWebcasts = suggestion.existing_webcasts ?? [];
  const eventDates = formatEventDateRange(
    suggestion.event?.start_date,
    suggestion.event?.end_date,
  );
  return (
    <div className="flex flex-col gap-3">
      {!hideEventContext && (
        <>
          <FieldRow label="Event">
            <ReferenceLink suggestion={suggestion} />
            {eventDates ? ` (${eventDates})` : ''}
          </FieldRow>
          <FieldRow label="Existing webcasts">
            {existingWebcasts.length > 0
              ? existingWebcasts
                  .map((webcast) =>
                    [webcast.type, webcast.channel, webcast.file]
                      .filter(Boolean)
                      .join(' / '),
                  )
                  .join(', ')
              : 'None yet!'}
          </FieldRow>
        </>
      )}
      {webcastUrl && (
        <FieldRow label="Suggested URL">
          <ExternalLink href={webcastUrl}>{webcastUrl}</ExternalLink>
        </FieldRow>
      )}
      {suggestion.uses_official_webcast_unit && (
        <Badge variant="destructive" className="w-fit">
          District uses the Official Webcast Unit
        </Badge>
      )}
      <div className="grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-muted-foreground">Type</span>
          <select
            className="h-9 rounded-md border border-input bg-transparent px-3
              text-sm"
            value={overrides.webcast_type ?? webcastDict?.type ?? ''}
            onChange={(e) =>
              onOverridesChange({ ...overrides, webcast_type: e.target.value })
            }
          >
            <option value="">choose...</option>
            {WEBCAST_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <LabeledInput
          label="Channel"
          value={overrides.webcast_channel ?? webcastDict?.channel ?? ''}
          onChange={(value) =>
            onOverridesChange({ ...overrides, webcast_channel: value })
          }
        />
        <LabeledInput
          label="File (optional)"
          value={overrides.webcast_file ?? webcastDict?.file ?? ''}
          onChange={(value) =>
            onOverridesChange({ ...overrides, webcast_file: value })
          }
        />
        <LabeledInput
          label="Date (optional)"
          placeholder="YYYY-MM-DD"
          value={
            overrides.webcast_date ?? contentsString(suggestion, 'webcast_date')
          }
          onChange={(value) =>
            onOverridesChange({ ...overrides, webcast_date: value })
          }
        />
      </div>
    </div>
  );
}

function OffseasonEventDetails({
  suggestion,
  overrides,
  onOverridesChange,
}: SuggestionReviewCardProps): JSX.Element {
  const field = (key: keyof AcceptRequest, contentsKey: string): string => {
    const overrideValue = overrides[key];
    if (typeof overrideValue === 'string') return overrideValue;
    return contentsString(suggestion, contentsKey);
  };
  const setField = (key: keyof AcceptRequest) => (value: string) =>
    onOverridesChange({ ...overrides, [key]: value });
  const similarSets = [
    { label: 'Similar events this year', events: suggestion.similar_events },
    {
      label: 'Similar events last year',
      events: suggestion.similar_events_last_year,
    },
  ];
  const startDate = field('start_date', 'start_date');
  const suggestedYear = /^\d{4}/.test(startDate)
    ? startDate.slice(0, 4)
    : String(Temporal.Now.plainDateISO().year);
  const firstCodeCandidate =
    field('first_code', 'first_code') || overrides.event_short || '';
  return (
    <div className="flex flex-col gap-3">
      {similarSets.map(
        ({ label, events }) =>
          (events ?? []).length > 0 && (
            <div
              key={label}
              className="rounded-lg border border-yellow-500 bg-yellow-500/10
                p-2 text-sm"
            >
              <span className="font-medium">{label}:</span>
              <ul className="mt-1 list-inside list-disc">
                {(events ?? []).map((event) => (
                  <li key={event.key}>
                    <Link
                      to="/event/$eventKey"
                      params={{ eventKey: event.key ?? '' }}
                      className="text-foreground underline underline-offset-2"
                    >
                      {event.name} ({event.key})
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ),
      )}
      <div className="grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-3">
        <LabeledInput
          label="Event short (required, e.g. 'cc')"
          value={overrides.event_short ?? ''}
          onChange={setField('event_short')}
        />
        <LabeledInput
          label="Name"
          value={field('name', 'name')}
          onChange={setField('name')}
        />
        <LabeledInput
          label="Short name"
          value={overrides.short_name ?? ''}
          onChange={setField('short_name')}
        />
        <LabeledInput
          label="Start date"
          placeholder="YYYY-MM-DD"
          value={field('start_date', 'start_date')}
          onChange={setField('start_date')}
        />
        <LabeledInput
          label="End date"
          placeholder="YYYY-MM-DD"
          value={field('end_date', 'end_date')}
          onChange={setField('end_date')}
        />
        <LabeledInput
          label="Website"
          value={field('website', 'website')}
          onChange={setField('website')}
        />
        <LabeledInput
          label="Venue"
          value={field('venue', 'venue_name')}
          onChange={setField('venue')}
        />
        <LabeledInput
          label="Address"
          value={field('venue_address', 'address')}
          onChange={setField('venue_address')}
        />
        <LabeledInput
          label="City"
          value={field('city', 'city')}
          onChange={setField('city')}
        />
        <LabeledInput
          label="State"
          value={field('state', 'state')}
          onChange={setField('state')}
        />
        <LabeledInput
          label="Country"
          value={field('country', 'country')}
          onChange={setField('country')}
        />
        <LabeledInput
          label="FIRST code (official events only)"
          value={field('first_code', 'first_code')}
          onChange={setField('first_code')}
        />
      </div>
      {firstCodeCandidate && (
        <FieldRow label="FIRST page preview">
          <ExternalLink
            href={`https://frc-events.firstinspires.org/${suggestedYear}/${firstCodeCandidate.toUpperCase()}`}
          >
            frc-events.firstinspires.org/{suggestedYear}/
            {firstCodeCandidate.toUpperCase()}
          </ExternalLink>{' '}
          <span className="text-muted-foreground">
            — if FIRST has a page here, the event short likely doubles as the
            FIRST code
          </span>
        </FieldRow>
      )}
    </div>
  );
}

function ApiWriteDetails({
  suggestion,
  overrides,
  onOverridesChange,
}: SuggestionReviewCardProps): JSX.Element {
  const requestedTypes = (suggestion.requested_auth_types ?? [])
    .map((authType) => authType.type)
    .filter((type): type is number => type !== undefined);
  const selectedTypes = overrides.auth_types ?? requestedTypes;
  const toggleType = (type: number, checked: boolean) => {
    const next = checked
      ? [...selectedTypes.filter((t) => t !== type), type]
      : selectedTypes.filter((t) => t !== type);
    onOverridesChange({ ...overrides, auth_types: next });
  };
  return (
    <div className="flex flex-col gap-3">
      <FieldRow label="Event">
        <ReferenceLink suggestion={suggestion} />
      </FieldRow>
      <FieldRow label="User">
        {suggestion.author?.nickname ?? 'unknown'}
      </FieldRow>
      <FieldRow label="Email">{suggestion.author?.email ?? 'unknown'}</FieldRow>
      <FieldRow label="Affiliation">
        {contentsString(suggestion, 'affiliation')}
      </FieldRow>
      {(suggestion.existing_auth ?? []).length > 0 && (
        <div
          className="rounded-lg border border-yellow-500 bg-yellow-500/10 p-2
            text-sm"
        >
          <span className="font-medium">
            Existing keys already granted for this event:
          </span>
          <ul className="list-inside list-disc">
            {(suggestion.existing_auth ?? []).map((auth, i) => (
              <li key={i}>
                {auth.owner_email ?? 'unknown owner'} (
                {(auth.auth_types ?? []).map((t) => t.name).join(', ')})
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-muted-foreground">
          Auth types to grant (requested types pre-checked):
        </span>
        <div className="flex flex-col gap-1">
          {WRITE_AUTH_TYPES.map((authType) => (
            <div key={authType.type} className="flex items-center gap-1">
              <Checkbox
                id={`auth-${suggestion.key}-${authType.type}`}
                checked={selectedTypes.includes(authType.type)}
                onCheckedChange={(checked) =>
                  toggleType(authType.type, checked === true)
                }
              />
              <label htmlFor={`auth-${suggestion.key}-${authType.type}`}>
                {authType.name}
              </label>
            </div>
          ))}
        </div>
      </div>
      <div className="max-w-48">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-muted-foreground">Expiration</span>
          <select
            className="h-9 rounded-md border border-input bg-transparent px-3
              text-sm"
            value={String(
              overrides.expiration_days ??
                defaultExpirationDays(suggestion.event?.end_date),
            )}
            onChange={(e) =>
              onOverridesChange({
                ...overrides,
                expiration_days: Number(e.target.value),
              })
            }
          >
            <option value="-1">Never expires</option>
            <option value="7">Event end + 7 days</option>
            <option value="30">Event end + 30 days</option>
            <option value="365">Event end + 1 year</option>
          </select>
        </label>
      </div>
      <label className="flex max-w-xl flex-col gap-1 text-sm">
        <span className="font-medium text-muted-foreground">
          Message for the user (included in the admin alert email)
        </span>
        <textarea
          className="min-h-20 rounded-md border border-input bg-transparent p-2
            text-sm"
          value={
            overrides.user_message ?? 'Thanks for helping make TBA better!'
          }
          onChange={(e) =>
            onOverridesChange({ ...overrides, user_message: e.target.value })
          }
        />
      </label>
    </div>
  );
}

const DETAIL_COMPONENTS: Record<
  string,
  (props: SuggestionReviewCardProps) => JSX.Element
> = {
  match: MatchVideoDetails,
  media: TeamMediaDetails,
  'social-media': SocialMediaDetails,
  robot: RobotCadDetails,
  event_media: EventMediaDetails,
  event: WebcastDetails,
  'offseason-event': OffseasonEventDetails,
  api_auth_access: ApiWriteDetails,
};

// Types whose suggestions target a team; the team becomes the card header
const TEAM_HEADER_TYPES = new Set(['media', 'social-media', 'robot']);

export function SuggestionReviewCard(
  props: SuggestionReviewCardProps,
): JSX.Element {
  const { suggestion, decision, onDecisionChange, focused } = props;
  const Details = DETAIL_COMPONENTS[suggestion.target_model];
  const reputation = suggestion.author
    ? formatAuthorReputation(suggestion.author)
    : undefined;
  return (
    <Card
      className={cn(
        'flex scroll-mt-24 flex-col gap-3 p-4',
        // Keyboard-focus glow, distinct from the browser focus ring
        focused &&
          `shadow-lg ring-2 shadow-primary/25 ring-primary/70 ring-offset-2
          ring-offset-background`,
      )}
      data-testid={`suggestion-${suggestion.key}`}
      data-decision={decision ?? 'none'}
      data-focused={focused ? 'true' : undefined}
    >
      {TEAM_HEADER_TYPES.has(suggestion.target_model) && (
        <CardHeader className="border-b p-0 pb-3">
          <CardTitle className="text-lg">
            <ReferenceLink suggestion={suggestion} />
          </CardTitle>
        </CardHeader>
      )}
      {Details && <Details {...props} />}
      <div
        className="flex flex-wrap items-center justify-between gap-2 border-t
          pt-3"
      >
        <div className="text-xs text-muted-foreground">
          Suggested by {suggestion.author?.nickname ?? 'unknown'}
          {suggestion.author?.email ? ` (${suggestion.author.email})` : ''}
          {suggestion.created ? ` on ${suggestion.created.slice(0, 10)}` : ''}
          {reputation ? ` · ${reputation}` : ''}
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={decision === 'accept' ? 'default' : 'outline'}
            className={
              decision === 'accept'
                ? 'bg-green-700 text-white hover:bg-green-800'
                : ''
            }
            onClick={() =>
              onDecisionChange(decision === 'accept' ? undefined : 'accept')
            }
          >
            (a)ccept
          </Button>
          <Button
            size="sm"
            variant={decision === 'reject' ? 'destructive' : 'outline'}
            onClick={() =>
              onDecisionChange(decision === 'reject' ? undefined : 'reject')
            }
          >
            (r)eject
          </Button>
        </div>
      </div>
    </Card>
  );
}
