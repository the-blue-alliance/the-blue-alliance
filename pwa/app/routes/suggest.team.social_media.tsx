import { useMutation, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';
import { type JSX, useState } from 'react';
import { z } from 'zod';

import { suggestTeamSocialMedia } from '~/api/tba/mobile/sdk.gen';
import type { TeamSocialMediaSuggestionResponse } from '~/api/tba/mobile/types.gen';
import {
  getTeamOptions,
  getTeamSocialMediaOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { useAuth } from '~/components/tba/auth/auth';
import SignInWithAppleButton from '~/components/tba/auth/signInWithAppleButton';
import SignInWithGoogleButton from '~/components/tba/auth/signInWithGoogleButton';
import SuggestionStatusMessage from '~/components/tba/suggestionStatusMessage';
import TeamSocialMediaList from '~/components/tba/teamSocialMediaList';
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
import { doThrowNotFound, publicCacheControlHeaders } from '~/lib/utils';

const searchSchema = z.object({
  team_key: z.string().catch(''),
});

export const Route = createFileRoute('/suggest/team/social_media')({
  validateSearch: searchSchema,
  loaderDeps: ({ search }) => search,
  loader: async ({ deps: { team_key }, context: { queryClient } }) => {
    if (!/^frc\d+$/.test(team_key)) {
      throw notFound();
    }

    await Promise.all([
      queryClient
        .ensureQueryData(getTeamOptions({ path: { team_key } }))
        .catch(doThrowNotFound),
      queryClient.ensureQueryData(
        getTeamSocialMediaOptions({ path: { team_key } }),
      ),
    ]);
  },
  headers: publicCacheControlHeaders(),
  component: SuggestTeamSocialMedia,
});

type SubmitStatus =
  'idle' | TeamSocialMediaSuggestionResponse['status'] | 'error'; // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

function SuggestTeamSocialMedia(): JSX.Element {
  const { team_key } = Route.useSearch();
  const { user } = useAuth();
  const [mediaUrl, setMediaUrl] = useState('');
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [loginOpen, setLoginOpen] = useState(false);

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key } }),
  );
  const { data: socials } = useSuspenseQuery(
    getTeamSocialMediaOptions({ path: { team_key } }),
  );

  const { mutate: submitMedia, isPending } = useMutation({
    mutationFn: async (url: string) => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const { data } = await suggestTeamSocialMedia({
        auth: token,
        body: { team_key, media_url: url },
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
        <h1 className="text-2xl font-semibold">Add Social Media</h1>
        <p className="text-lg text-muted-foreground">
          Team {team.team_number}
          {team.nickname ? ` — ${team.nickname}` : ''}
        </p>
      </div>

      {status === 'success' && (
        <SuggestionStatusMessage tone="success" title="Thanks!">
          We&apos;ll review your suggestion and get it added to the site soon!
        </SuggestionStatusMessage>
      )}
      {status === 'media_exists' && (
        <SuggestionStatusMessage tone="info" title="Already approved">
          The URL you submitted has already been approved.
        </SuggestionStatusMessage>
      )}
      {status === 'suggestion_exists' && (
        <SuggestionStatusMessage tone="info" title="Already pending">
          The URL you submitted is already pending review.
        </SuggestionStatusMessage>
      )}
      {status === 'bad_url' && (
        <SuggestionStatusMessage tone="error" title="Unsupported URL">
          We can&apos;t support the URL you submitted. Check the supported
          formats below.
        </SuggestionStatusMessage>
      )}
      {(status === 'error' ||
        status === 'bad_team' ||
        status === 'unauthorized') && (
        <SuggestionStatusMessage tone="error" title="Something went wrong">
          Please try again.
        </SuggestionStatusMessage>
      )}

      <div className="space-y-2">
        <p>
          Thanks for helping make The Blue Alliance better! Let us know about
          this team&apos;s social media accounts so we can add them to the site.
        </p>
        <ul className="list-disc pl-6 text-sm text-muted-foreground">
          <li>Your suggestion will be reviewed by a moderator.</li>
        </ul>
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Supported formats</h2>
        <ul className="list-disc space-y-1 pl-6 text-sm text-muted-foreground">
          <li>
            <strong className="text-foreground">Facebook pages</strong>, like{' '}
            <code>https://facebook.com/theuberbots</code>
          </li>
          <li>
            <strong className="text-foreground">Twitter profiles</strong>, like{' '}
            <code>https://twitter.com/team1124</code>
          </li>
          <li>
            <strong className="text-foreground">YouTube channels</strong>, like{' '}
            <code>https://www.youtube.com/user/Uberbots1124</code>. We can only
            accept channels with a custom URL.{' '}
            <a
              href="https://support.google.com/youtube/answer/2657968?hl=en"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-4"
            >
              Here&apos;s how to create one
            </a>
            .
          </li>
          <li>
            <strong className="text-foreground">GitHub accounts</strong>, like{' '}
            <code>https://github.com/frc1124</code>
          </li>
          <li>
            <strong className="text-foreground">GitLab accounts</strong>, like{' '}
            <code>https://gitlab.com/frc1124</code>
          </li>
          <li>
            <strong className="text-foreground">Instagram profiles</strong>,
            like <code>https://www.instagram.com/4hteamneutrino</code>
          </li>
        </ul>
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">
          Existing social media accounts
        </h2>
        {socials.length > 0 ? (
          <TeamSocialMediaList socials={socials} />
        ) : (
          <p className="text-sm text-muted-foreground">
            No existing social media accounts.
          </p>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-semibold">Add social media</h2>
        {!user && (
          <p className="mb-2 text-sm text-muted-foreground">
            You must be signed in to suggest social media.
          </p>
        )}
        <form
          onSubmit={(e) => handleSubmit(e)}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <Input
            type="url"
            aria-label="Social media URL"
            placeholder="https://facebook.com/theuberbots"
            value={mediaUrl}
            onChange={(e) => setMediaUrl(e.target.value)}
            required
            className="flex-1"
          />
          <Button type="submit" disabled={isPending}>
            {isPending ? 'Submitting…' : 'Add Social Media'}
          </Button>
        </form>
      </div>

      <Credenza open={loginOpen} onOpenChange={setLoginOpen}>
        <CredenzaContent className="max-h-[85vh] overflow-y-auto">
          <CredenzaHeader>
            <CredenzaTitle>Sign in to suggest social media</CredenzaTitle>
            <CredenzaDescription>
              You need to be signed in to suggest social media for Team{' '}
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
