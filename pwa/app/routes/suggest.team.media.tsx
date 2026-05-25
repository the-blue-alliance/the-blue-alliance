import { useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';
import { type JSX, useState } from 'react';
import { z } from 'zod';

import { suggestTeamMedia } from '~/api/tba/mobile/sdk.gen';
import {
  getTeamMediaByYearOptions,
  getTeamOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import SignInWithAppleButton from '~/components/tba/auth/signInWithAppleButton';
import SignInWithGoogleButton from '~/components/tba/auth/signInWithGoogleButton';
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
import { publicCacheControlHeaders } from '~/lib/utils';

const searchSchema = z.object({
  team_key: z.string().catch(''),
  year: z.number().int().catch(0),
});

export const Route = createFileRoute('/suggest/team/media')({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => search,
  loader: async ({ deps: { team_key, year }, context: { queryClient } }) => {
    if (!/^frc\d+$/.test(team_key)) {
      throw notFound();
    }
    await Promise.all([
      queryClient.ensureQueryData(getTeamOptions({ path: { team_key } })),
      queryClient.ensureQueryData(
        getTeamMediaByYearOptions({ path: { team_key, year } }),
      ),
    ]);
  },
  headers: publicCacheControlHeaders(),
  component: SuggestTeamMedia,
});

type SubmitStatus =
  | 'idle'
  | 'loading'
  | 'success'
  | 'exists'
  | 'bad_url'
  | 'error';

function SuggestTeamMedia(): JSX.Element {
  const { team_key, year } = Route.useSearch();
  const { user } = useAuth();
  const [mediaUrl, setMediaUrl] = useState('');
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [loginOpen, setLoginOpen] = useState(false);

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key } }),
  );
  const { data: media } = useSuspenseQuery(
    getTeamMediaByYearOptions({ path: { team_key, year } }),
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setLoginOpen(true);
      return;
    }
    setStatus('loading');
    try {
      const token = await user.getIdToken();
      const { data } = await suggestTeamMedia({
        auth: token,
        body: {
          reference_type: 'team',
          reference_key: team_key,
          year,
          media_url: mediaUrl,
          details_json: '',
        },
      });
      const code = Number(data?.code);
      if (code === 200) {
        setStatus('success');
        setMediaUrl('');
      } else if (code === 304) {
        setStatus('exists');
      } else if (code === 400) {
        setStatus('bad_url');
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  };

  return (
    <div className="mx-auto max-w-2xl py-8">
      <h1 className="mb-2 text-2xl font-semibold">
        Add Media for Team {team.team_number}
        {team.nickname ? ` \u2014 ${team.nickname}` : ''} ({year})
      </h1>

      {status === 'success' && (
        <div
          className="mb-4 rounded-lg border border-green-300 bg-green-50 p-4
            text-green-900 dark:border-green-800 dark:bg-green-950
            dark:text-green-100"
        >
          <p className="font-semibold">Thanks!</p>
          <p className="text-sm">
            We&apos;ll review your suggestion and get it added to the site soon!
          </p>
        </div>
      )}
      {status === 'exists' && (
        <div
          className="mb-4 rounded-lg border border-blue-300 bg-blue-50 p-4
            text-blue-900 dark:border-blue-800 dark:bg-blue-950
            dark:text-blue-100"
        >
          <p className="font-semibold">Already submitted</p>
          <p className="text-sm">This URL has already been submitted.</p>
        </div>
      )}
      {status === 'bad_url' && (
        <div
          className="mb-4 rounded-lg border border-red-300 bg-red-50 p-4
            text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100"
        >
          <p className="font-semibold">Unsupported URL</p>
          <p className="text-sm">
            Sorry, we can&apos;t support the URL you submitted. See below for
            supported formats.
          </p>
        </div>
      )}
      {status === 'error' && (
        <div
          className="mb-4 rounded-lg border border-red-300 bg-red-50 p-4
            text-red-900 dark:border-red-800 dark:bg-red-950 dark:text-red-100"
        >
          <p className="font-semibold">Something went wrong</p>
          <p className="text-sm">Please try again.</p>
        </div>
      )}

      <div className="mb-6">
        <p className="mb-2">
          Thanks for helping make The Blue Alliance better! Let us know about
          media so we can add them to the site!
        </p>
        <ul className="list-disc pl-6 text-sm text-muted-foreground">
          <li>Your suggestion will be reviewed by a moderator.</li>
          <li>
            Please include media that clearly identifies the team (bumpers,
            banners, logos, etc.).
          </li>
        </ul>
      </div>

      <div className="mb-6">
        <h2 className="mb-2 text-lg font-semibold">Supported formats</h2>
        <ul className="list-disc pl-6 text-sm text-muted-foreground">
          <li>
            <strong className="text-foreground">Imgur images</strong>, like{' '}
            <code>http://imgur.com/aF8T5ZE</code> (not albums with{' '}
            <code>/a/</code> in their URL)
          </li>
          <li>
            <strong className="text-foreground">Instagram photos/videos</strong>
            , like <code>https://www.instagram.com/p/BUnZiriBYre</code>
          </li>
          <li>
            <strong className="text-foreground">YouTube videos</strong>, like{' '}
            <code>https://www.youtube.com/watch?v=DojyJ9bZ4fk</code>
          </li>
          <li>
            <strong className="text-foreground">GrabCAD files</strong>, like{' '}
            <code>https://grabcad.com/library/cad-stuff</code>
          </li>
          <li>
            <strong className="text-foreground">Onshape documents</strong> that
            are publicly accessible via link
          </li>
          <li>
            <strong className="text-foreground">
              Chief Delphi build/technical threads
            </strong>
          </li>
        </ul>
      </div>

      {media.length > 0 && (
        <div className="mb-6">
          <h2 className="mb-2 text-lg font-semibold">
            Existing Media ({media.length})
          </h2>
          <ul className="list-disc pl-6 text-sm text-muted-foreground">
            {media.map((m, i) => (
              <li key={i}>{m.type}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mb-4">
        <h2 className="mb-2 text-lg font-semibold">Add media</h2>
        {!user && (
          <p className="mb-2 text-sm text-muted-foreground">
            You must be signed in to suggest media.
          </p>
        )}
        <form
          onSubmit={(e) => {
            void handleSubmit(e);
          }}
          className="flex gap-2"
        >
          <Input
            type="url"
            placeholder="https://imgur.com/aF8T5ZE"
            value={mediaUrl}
            onChange={(e) => setMediaUrl(e.target.value)}
            required
            className="flex-1"
          />
          <Button type="submit" disabled={status === 'loading'}>
            {status === 'loading' ? 'Submitting\u2026' : 'Add Media'}
          </Button>
        </form>
      </div>

      <Credenza open={loginOpen} onOpenChange={setLoginOpen}>
        <CredenzaContent className="max-h-[85vh] overflow-y-auto">
          <CredenzaHeader>
            <CredenzaTitle>Sign in to suggest media</CredenzaTitle>
            <CredenzaDescription>
              You need to be signed in to suggest media for Team{' '}
              {team.team_number}.
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
