import { useMutation, useSuspenseQuery } from '@tanstack/react-query';
import { Link, createFileRoute, notFound } from '@tanstack/react-router';
import { type JSX, useState } from 'react';
import { z } from 'zod';

import {
  resolveVideoPlaylist,
  suggestEventMatchVideos,
} from '~/api/tba/mobile/sdk.gen';
import type { EventMatchVideo } from '~/api/tba/mobile/types.gen';
import { getEventOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import SignInDialog from '~/components/tba/auth/signInDialog';
import LoadingSkeleton from '~/components/tba/loadingSkeleton';
import MatchVideoGuidelines from '~/components/tba/matchVideoGuidelines';
import SuggestionStatusMessage from '~/components/tba/suggestionStatusMessage';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { isValidEventKey } from '~/lib/eventUtils';
import { doThrowNotFound, publicCacheControlHeaders } from '~/lib/utils';

const searchSchema = z.object({
  event_key: z.string().catch(''),
});

export const Route = createFileRoute('/suggest/event/video')({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => search,
  loader: async ({ deps: { event_key }, context: { queryClient } }) => {
    if (!isValidEventKey(event_key)) {
      throw notFound();
    }

    await queryClient
      .ensureQueryData(getEventOptions({ path: { event_key } }))
      .catch(doThrowNotFound);
  },
  headers: publicCacheControlHeaders(),
  component: SuggestEventVideos,
});

interface PlaylistVideo extends EventMatchVideo {
  video_title: string;
}

function playlistIdFromUrl(url: string): string | null {
  return URL.canParse(url) ? new URL(url).searchParams.get('list') : null;
}

function SuggestEventVideos(): JSX.Element {
  const { event_key } = Route.useSearch();
  const { user } = useAuth();
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [playlistError, setPlaylistError] = useState<
    'invalid_url' | 'load_failed' | null
  >(null);
  const [videos, setVideos] = useState<PlaylistVideo[]>([]);
  const [submitStatus, setSubmitStatus] = useState<
    { numAdded: number } | 'error' | null
  >(null);
  const [loginOpen, setLoginOpen] = useState(false);

  const { data: event } = useSuspenseQuery(
    getEventOptions({ path: { event_key } }),
  );

  const { mutate: loadPlaylist, isPending: isLoading } = useMutation({
    mutationFn: async (playlistId: string) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const { data } = await resolveVideoPlaylist({
        auth: token,
        body: { playlist_id: playlistId },
      });
      if (data?.code !== 200) throw new Error('Unable to load playlist');
      return data.videos;
    },
    onSuccess: (playlistVideos) =>
      setVideos(
        playlistVideos.map((v) => ({
          video_id: v.video_id,
          video_title: v.video_title,
          match_partial: v.guessed_match_partial,
        })),
      ),
    onError: () => setPlaylistError('load_failed'),
  });

  const { mutate: submitVideos, isPending: isSubmitting } = useMutation({
    mutationFn: async (toSubmit: EventMatchVideo[]) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const { data } = await suggestEventMatchVideos({
        auth: token,
        body: { event_key, videos: toSubmit },
      });
      if (data?.status !== 'success') throw new Error('Suggestion failed');
      return data.num_added;
    },
    onSuccess: (numAdded) => {
      setSubmitStatus({ numAdded });
      setVideos([]);
      setPlaylistUrl('');
    },
    onError: () => setSubmitStatus('error'),
  });

  const handleLoad = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setLoginOpen(true);
      return;
    }
    setPlaylistError(null);
    setSubmitStatus(null);
    setVideos([]);
    const playlistId = playlistIdFromUrl(playlistUrl);
    if (!playlistId) {
      setPlaylistError('invalid_url');
      return;
    }
    loadPlaylist(playlistId);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setLoginOpen(true);
      return;
    }
    setSubmitStatus(null);
    submitVideos(
      videos.map((v) => ({
        video_id: v.video_id,
        match_partial: v.match_partial.trim(),
      })),
    );
  };

  const setMatchPartial = (index: number, matchPartial: string) =>
    setVideos((current) =>
      current.map((v, i) =>
        i === index ? { ...v, match_partial: matchPartial } : v,
      ),
    );

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Add Match Videos</h1>
        <p className="text-lg text-muted-foreground">
          <Link
            to="/event/$eventKey"
            params={{ eventKey: event_key }}
            className="hover:underline"
          >
            {event.year} {event.name}
          </Link>
        </p>
      </div>

      {submitStatus === 'error' && (
        <SuggestionStatusMessage tone="error" title="Something went wrong">
          Please try again.
        </SuggestionStatusMessage>
      )}
      {submitStatus !== null && submitStatus !== 'error' && (
        <SuggestionStatusMessage tone="success" title="Thanks!">
          Added {submitStatus.numAdded} new suggestions. We&apos;ll review them
          and get them added to the site soon!
        </SuggestionStatusMessage>
      )}

      <div className="space-y-2">
        <p>
          Thanks for helping make The Blue Alliance better! Paste a YouTube
          playlist of match videos from this event, check the match for each
          video, then submit them all at once.
        </p>
        <MatchVideoGuidelines />
      </div>

      <div className="space-y-2 rounded-lg border p-4 text-sm">
        <h2 className="font-semibold">Match IDs</h2>
        <p>
          A match ID is the match type followed by <code>m</code> and the match
          number. Leave it blank to skip a video, for example an award ceremony.
        </p>
        <ul className="list-disc space-y-1 pl-6">
          <li>
            <code>qm3</code>: Qualification Match 3
          </li>
          <li>
            <code>qf2m1</code>: Quarterfinal 2, Match 1
          </li>
          <li>
            <code>sf1m3</code>: Semifinal 1, Match 3
          </li>
          <li>
            <code>f1m3</code>: Finals Match 3
          </li>
          <li>
            Double elimination: <code>sf</code>, the match number, then{' '}
            <code>m1</code>. For example, <code>sf2m1</code> is Match 2.
          </li>
          <li>
            Round robin: <code>sf1m</code> and the match number. For example,{' '}
            <code>sf1m6</code> is Round Robin Match 6.
          </li>
        </ul>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-semibold">YouTube playlist</h2>
        {!user && (
          <p className="text-sm text-muted-foreground">
            You must be signed in to suggest videos.
          </p>
        )}
        <form
          onSubmit={(e) => handleLoad(e)}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <Input
            type="url"
            aria-label="YouTube playlist URL"
            placeholder="https://www.youtube.com/playlist?list=PLLDODAGuIHqNRyZPxoHlvwMsJYP79ptCv"
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            required
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading}>
            {isLoading ? 'Loading…' : 'Load Playlist'}
          </Button>
        </form>
        {playlistError === 'invalid_url' && (
          <SuggestionStatusMessage tone="error" title="Invalid playlist URL">
            Use a link that contains <code>list=</code>, like the example above.
          </SuggestionStatusMessage>
        )}
        {playlistError === 'load_failed' && (
          <SuggestionStatusMessage tone="error" title="Couldn't load playlist">
            Check that the playlist is public and try again.
          </SuggestionStatusMessage>
        )}
      </div>

      {isLoading && (
        <LoadingSkeleton label="Loading playlist" className="h-40" />
      )}

      {videos.length > 0 && (
        <form onSubmit={(e) => handleSubmit(e)} className="space-y-4">
          <h2 className="text-lg font-semibold">
            Videos in playlist ({videos.length})
          </h2>
          <ol className="divide-y rounded-lg border">
            {videos.map((v, i) => (
              <li
                key={`${v.video_id}-${i}`}
                className="flex flex-col gap-2 p-3 sm:flex-row sm:items-center"
              >
                <a
                  href={`https://youtu.be/${v.video_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 hover:underline"
                >
                  {v.video_title}
                </a>
                <Input
                  aria-label={`Match ID for ${v.video_title}`}
                  placeholder="Match ID"
                  value={v.match_partial}
                  onChange={(e) => setMatchPartial(i, e.target.value)}
                  className="sm:w-32"
                />
              </li>
            ))}
          </ol>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting…' : 'Add Suggestions'}
          </Button>
        </form>
      )}

      <SignInDialog
        open={loginOpen}
        onOpenChange={setLoginOpen}
        title="Sign in to suggest videos"
        description={`You need to be signed in to suggest videos for ${event.name}.`}
      />
    </div>
  );
}
