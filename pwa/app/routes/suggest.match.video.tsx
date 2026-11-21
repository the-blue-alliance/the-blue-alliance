import { useMutation, useSuspenseQuery } from '@tanstack/react-query';
import { Link, createFileRoute, notFound } from '@tanstack/react-router';
import { type JSX, useState } from 'react';
import { z } from 'zod';

import { suggestMatchVideo } from '~/api/tba/mobile/sdk.gen';
import type { MatchVideoSuggestionResponse } from '~/api/tba/mobile/types.gen';
import { PlayoffType } from '~/api/tba/read';
import {
  getEventOptions,
  getMatchOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import SignInDialog from '~/components/tba/auth/signInDialog';
import MatchVideoGuidelines from '~/components/tba/matchVideoGuidelines';
import SuggestionStatusMessage from '~/components/tba/suggestionStatusMessage';
import { YoutubeEmbed } from '~/components/tba/videoEmbeds';
import { Button, buttonVariants } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { isValidMatchKey, matchTitleShort } from '~/lib/matchUtils';
import { doThrowNotFound, publicCacheControlHeaders } from '~/lib/utils';

const searchSchema = z.object({
  match_key: z.string().catch(''),
});

export const Route = createFileRoute('/suggest/match/video')({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => search,
  loader: async ({ deps: { match_key }, context: { queryClient } }) => {
    if (!isValidMatchKey(match_key)) {
      throw notFound();
    }

    await Promise.all([
      queryClient
        .ensureQueryData(
          getEventOptions({ path: { event_key: match_key.split('_')[0] } }),
        )
        .catch(doThrowNotFound),
      queryClient
        .ensureQueryData(getMatchOptions({ path: { match_key } }))
        .catch(doThrowNotFound),
    ]);
  },
  headers: publicCacheControlHeaders(),
  component: SuggestMatchVideo,
});

type SubmitStatus = 'idle' | MatchVideoSuggestionResponse['status'] | 'error'; // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

function SuggestMatchVideo(): JSX.Element {
  const { match_key } = Route.useSearch();
  const { user } = useAuth();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [loginOpen, setLoginOpen] = useState(false);

  const { data: match } = useSuspenseQuery(
    getMatchOptions({ path: { match_key } }),
  );
  const { data: event } = useSuspenseQuery(
    getEventOptions({ path: { event_key: match.event_key } }),
  );
  const title = matchTitleShort(
    match,
    event.playoff_type ?? PlayoffType.CUSTOM,
  );
  const videos = match.videos.filter((v) => v.type === 'youtube');
  const searchQuery = encodeURIComponent(
    `${title} ${event.year} ${event.name}`,
  );

  const { mutate: submitVideo, isPending } = useMutation({
    mutationFn: async (url: string) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const { data } = await suggestMatchVideo({
        auth: token,
        body: { match_key, youtube_url: url },
      });
      if (!data) throw new Error('Missing suggestion response');
      return data;
    },
    onSuccess: (response) => {
      setStatus(response.status);
      if (response.status === 'success') {
        setYoutubeUrl('');
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
    submitVideo(youtubeUrl);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Add Match Video</h1>
        <p className="text-lg text-muted-foreground">
          <Link
            to="/match/$matchKey"
            params={{ matchKey: match_key }}
            className="hover:underline"
          >
            {title}
          </Link>{' '}
          – {event.year} {event.name}
        </p>
      </div>

      {status === 'success' && (
        <SuggestionStatusMessage tone="success" title="Thanks!">
          We&apos;ll review your suggestion and get it added to the site soon!
        </SuggestionStatusMessage>
      )}
      {status === 'video_exists' && (
        <SuggestionStatusMessage tone="info" title="Already approved">
          The video you submitted has already been approved.
        </SuggestionStatusMessage>
      )}
      {status === 'suggestion_exists' && (
        <SuggestionStatusMessage tone="info" title="Already pending">
          The video you submitted is already pending review.
        </SuggestionStatusMessage>
      )}
      {status === 'bad_url' && (
        <SuggestionStatusMessage tone="error" title="Unrecognized URL">
          We couldn&apos;t recognize the URL you submitted. Make sure it is a
          YouTube video link.
        </SuggestionStatusMessage>
      )}
      {(status === 'error' ||
        status === 'bad_match' ||
        status === 'unauthorized') && (
        <SuggestionStatusMessage tone="error" title="Something went wrong">
          Please try again.
        </SuggestionStatusMessage>
      )}

      <div className="space-y-2">
        <p>
          Thanks for helping make The Blue Alliance better! Let us know about
          videos of this match so we can add them to the site.
        </p>
        <MatchVideoGuidelines />
        <p className="text-sm">
          Have a playlist with many videos from this event?{' '}
          <Link
            to="/suggest/event/video"
            search={{ event_key: match.event_key }}
            className="underline underline-offset-4"
          >
            Add them all at once
          </Link>
          .
        </p>
      </div>

      {videos.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">
            Videos on The Blue Alliance ({videos.length})
          </h2>
          <div
            className="grid
              grid-cols-[repeat(auto-fill,minmax(min(100%,22rem),1fr))] gap-4"
          >
            {videos.map((v) => (
              <YoutubeEmbed key={v.key} videoId={v.key} title={v.key} />
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <h2 className="text-lg font-semibold">
          {videos.length > 0 ? 'Add another video' : 'Add a video'}
        </h2>
        {!user && (
          <p className="text-sm text-muted-foreground">
            You must be signed in to suggest videos.
          </p>
        )}
        <form
          onSubmit={(e) => handleSubmit(e)}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <Input
            type="url"
            aria-label="YouTube URL"
            placeholder="https://www.youtube.com/watch?v=MQ0VNzIvHx0"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            required
            className="flex-1"
          />
          <Button type="submit" disabled={isPending}>
            {isPending ? 'Submitting…' : 'Add Video'}
          </Button>
        </form>
        <a
          href={`https://www.youtube.com/results?search_query=${searchQuery}`}
          target="_blank"
          rel="noopener noreferrer"
          className={buttonVariants({ variant: 'secondary' })}
        >
          Search YouTube for this match
        </a>
      </div>

      <SignInDialog
        open={loginOpen}
        onOpenChange={setLoginOpen}
        title="Sign in to suggest videos"
        description={`You need to be signed in to suggest videos for ${title}.`}
      />
    </div>
  );
}
