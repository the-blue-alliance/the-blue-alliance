import { useMutation, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';
import { type JSX, useState } from 'react';
import { z } from 'zod';

import { suggestEventMedia } from '~/api/tba/mobile/sdk.gen';
import type { EventMediaSuggestionResponse } from '~/api/tba/mobile/types.gen';
import {
  getEventMediaOptions,
  getEventOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import SignInWithAppleButton from '~/components/tba/auth/signInWithAppleButton';
import SignInWithGoogleButton from '~/components/tba/auth/signInWithGoogleButton';
import SmugmugAlbumGallery from '~/components/tba/smugmugAlbumGallery';
import { YoutubeEmbed } from '~/components/tba/videoEmbeds';
import { Button } from '~/components/ui/button';
import {
  Credenza,
  CredenzaBody,
  CredenzaContent,
  CredenzaDescription,
  CredenzaHeader,
  CredenzaTitle,
} from '~/components/ui/credenza';
import { Input } from '~/components/ui/input';
import { isValidEventKey } from '~/lib/eventUtils';
import { getEventVideos, getSmugmugAlbums } from '~/lib/mediaUtils';
import { doThrowNotFound, publicCacheControlHeaders } from '~/lib/utils';

const searchSchema = z.object({
  event_key: z.string().catch(''),
});

export const Route = createFileRoute('/suggest/event/media')({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => search,
  loader: async ({ deps: { event_key }, context: { queryClient } }) => {
    if (!isValidEventKey(event_key)) {
      throw notFound();
    }

    await Promise.all([
      queryClient
        .ensureQueryData(getEventOptions({ path: { event_key } }))
        .catch(doThrowNotFound),
      queryClient.ensureQueryData(
        getEventMediaOptions({ path: { event_key } }),
      ),
    ]);
  },
  headers: publicCacheControlHeaders(),
  component: SuggestEventMedia,
});

type SubmitStatus = 'idle' | EventMediaSuggestionResponse['status'] | 'error';

function SuggestEventMedia(): JSX.Element {
  const { event_key } = Route.useSearch();
  const { user } = useAuth();
  const [mediaUrl, setMediaUrl] = useState('');
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [loginOpen, setLoginOpen] = useState(false);

  const { data: event } = useSuspenseQuery(
    getEventOptions({ path: { event_key } }),
  );
  const { data: media } = useSuspenseQuery(
    getEventMediaOptions({ path: { event_key } }),
  );
  const videos = getEventVideos(media);
  const albums = getSmugmugAlbums(media);

  const { mutate: submitMedia, isPending } = useMutation({
    mutationFn: async (url: string) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const { data } = await suggestEventMedia({
        auth: token,
        body: { event_key, media_url: url },
      });
      if (!data) throw new Error('Missing suggestion response');
      return data;
    },
    onSuccess: (response) => {
      setStatus(response.status);
      if (response.status === 'success') {
        setMediaUrl('');
      }
    },
    onError: () => setStatus('error'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setLoginOpen(true);
      return;
    }
    setStatus('idle');
    submitMedia(mediaUrl);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 py-8">
      <div>
        <h1 className="text-2xl font-semibold">Add Event Media</h1>
        <p className="text-lg text-muted-foreground">
          {event.year} {event.name}
        </p>
      </div>

      {status === 'success' && (
        <StatusMessage tone="success" title="Thanks!">
          We&apos;ll review your suggestion and get it added to the site soon!
        </StatusMessage>
      )}
      {status === 'media_exists' && (
        <StatusMessage tone="info" title="Already approved">
          The URL you submitted has already been approved.
        </StatusMessage>
      )}
      {status === 'suggestion_exists' && (
        <StatusMessage tone="info" title="Already pending">
          The URL you submitted is already pending review.
        </StatusMessage>
      )}
      {status === 'bad_url' && (
        <StatusMessage tone="error" title="Unsupported URL">
          We can&apos;t support the URL you submitted. Check the supported
          formats below.
        </StatusMessage>
      )}
      {(status === 'error' ||
        status === 'bad_event' ||
        status === 'unauthorized') && (
        <StatusMessage tone="error" title="Something went wrong">
          Please try again.
        </StatusMessage>
      )}

      <div className="space-y-2">
        <p>
          Thanks for helping make The Blue Alliance better! Suggest media that
          helps the community experience this event.
        </p>
        <ul className="list-disc pl-6 text-sm text-muted-foreground">
          <li>Your suggestion will be reviewed by a moderator.</li>
          <li>
            Supported formats are YouTube videos and complete SmugMug albums.
          </li>
        </ul>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Guidance title="Please submit" tone="success">
          <li>Videos of award ceremonies</li>
          <li>Opening or closing ceremony speeches</li>
          <li>Community interviews and other engaging event content</li>
          <li>Complete SmugMug photo albums from the event</li>
        </Guidance>
        <Guidance title="Please do not submit" tone="error">
          <li>
            Full match videos; submit those through the{' '}
            <a
              href={`https://www.thebluealliance.com/suggest/event/video?event_key=${event_key}`}
              className="underline underline-offset-4"
            >
              match video form
            </a>
          </li>
          <li>Videos of people dancing</li>
          <li>Long videos with little event-related content</li>
          <li>Meme videos or individual SmugMug photos</li>
        </Guidance>
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Supported formats</h2>
        <ul className="list-disc space-y-1 pl-6 text-sm text-muted-foreground">
          <li>
            <strong className="text-foreground">YouTube videos</strong>, like{' '}
            <code>https://www.youtube.com/watch?v=pRaKQ0yCLJY</code>
          </li>
          <li>
            <strong className="text-foreground">SmugMug albums</strong>, like{' '}
            <code>https://nefirst.smugmug.com/2026-FIRST-AGE/2026-CMP-BAE</code>
          </li>
        </ul>
      </div>

      {(videos.length > 0 || albums.length > 0) && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">
            Existing Media ({media.length})
          </h2>
          {videos.length > 0 && (
            <div className="grid gap-4 sm:grid-cols-2">
              {videos.map((video) => (
                <YoutubeEmbed
                  key={video.foreign_key}
                  videoId={video.foreign_key}
                  title={video.foreign_key}
                />
              ))}
            </div>
          )}
          <SmugmugAlbumGallery albums={albums} />
        </div>
      )}

      <div>
        <h2 className="mb-2 text-lg font-semibold">Add media</h2>
        {!user && (
          <p className="mb-2 text-sm text-muted-foreground">
            You must be signed in to suggest media.
          </p>
        )}
        <form
          onSubmit={(e) => handleSubmit(e)}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <Input
            type="url"
            aria-label="Media URL"
            placeholder="https://www.youtube.com/watch?v=pRaKQ0yCLJY"
            value={mediaUrl}
            onChange={(e) => setMediaUrl(e.target.value)}
            required
            className="flex-1"
          />
          <Button type="submit" disabled={isPending}>
            {isPending ? 'Submitting…' : 'Add Media'}
          </Button>
        </form>
      </div>

      <Credenza open={loginOpen} onOpenChange={setLoginOpen}>
        <CredenzaContent className="max-h-[85vh] overflow-y-auto">
          <CredenzaHeader>
            <CredenzaTitle>Sign in to suggest media</CredenzaTitle>
            <CredenzaDescription>
              You need to be signed in to suggest media for {event.name}.
            </CredenzaDescription>
          </CredenzaHeader>
          <CredenzaBody>
            <div className="flex flex-col gap-2 py-2">
              <SignInWithGoogleButton />
              <SignInWithAppleButton />
            </div>
          </CredenzaBody>
        </CredenzaContent>
      </Credenza>
    </div>
  );
}

function StatusMessage({
  children,
  title,
  tone,
}: {
  children: React.ReactNode;
  title: string;
  tone: 'success' | 'info' | 'error';
}): JSX.Element {
  const colors = {
    success:
      'border-green-300 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950 dark:text-green-100',
    info: 'border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-800 dark:bg-blue-950 dark:text-blue-100',
    error:
      'border-red-300 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100',
  };
  return (
    <div role="alert" className={`rounded-lg border p-4 ${colors[tone]}`}>
      <p className="font-semibold">{title}</p>
      <p className="text-sm">{children}</p>
    </div>
  );
}

function Guidance({
  children,
  title,
  tone,
}: {
  children: React.ReactNode;
  title: string;
  tone: 'success' | 'error';
}): JSX.Element {
  const colors =
    tone === 'success'
      ? 'border-green-300 bg-green-50 dark:border-green-800 dark:bg-green-950'
      : 'border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-950';
  return (
    <div className={`rounded-lg border p-4 ${colors}`}>
      <h2 className="mb-2 font-semibold">{title}</h2>
      <ul className="list-disc space-y-1 pl-5 text-sm">{children}</ul>
    </div>
  );
}
