import { useMutation } from '@tanstack/react-query';
import { Link, createFileRoute } from '@tanstack/react-router';
import { type JSX, useState } from 'react';

import { requestApiWriteKey } from '~/api/tba/mobile/sdk.gen';
import type { ApiWriteKeyRequestResponse } from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import SuggestionStatusMessage from '~/components/tba/suggestionStatusMessage';
import { Button } from '~/components/ui/button';
import { Checkbox } from '~/components/ui/checkbox';
import { Input } from '~/components/ui/input';
import { Spinner } from '~/components/ui/spinner';

export const Route = createFileRoute('/request/apiwrite')({
  component: RequestApiWrite,
  head: () => ({
    meta: [
      { title: 'Request Write Keys - The Blue Alliance' },
      {
        name: 'description',
        content:
          'Request auth tokens to import your offseason event to The Blue Alliance',
      },
    ],
  }),
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

const WRITE_TYPES = [
  { id: 1, label: 'Match video' },
  { id: 2, label: 'Event teams' },
  { id: 3, label: 'Event matches' },
  { id: 4, label: 'Event rankings' },
  { id: 5, label: 'Event alliances' },
  { id: 6, label: 'Event awards' },
  { id: 7, label: 'Event info' },
  { id: 8, label: 'Zebra MotionWorks' },
];

type SubmitStatus = 'idle' | ApiWriteKeyRequestResponse['status'] | 'error';

function RequestApiWrite(): JSX.Element {
  const { isInitialLoading, user } = useAuth();
  const [eventKey, setEventKey] = useState('');
  const [affiliation, setAffiliation] = useState('');
  const [authTypes, setAuthTypes] = useState<number[]>([]);
  const [status, setStatus] = useState<SubmitStatus>('idle');

  const { mutate: submitRequest, isPending } = useMutation({
    mutationFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const { data } = await requestApiWriteKey({
        auth: token,
        body: {
          event_key: eventKey.trim(),
          affiliation: affiliation.trim(),
          auth_types: authTypes,
        },
      });
      if (!data) throw new Error('Missing request response');
      return data;
    },
    onSuccess: (response) => {
      setStatus(response.status);
      if (response.status === 'success') {
        setEventKey('');
        setAffiliation('');
        setAuthTypes([]);
      }
    },
    onError: () => setStatus('error'),
  });

  if (isInitialLoading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-8 text-muted-foreground" />
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const toggleAuthType = (id: number, checked: boolean) =>
    setAuthTypes((current) =>
      checked ? [...current, id] : current.filter((t) => t !== id),
    );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('idle');
    submitRequest();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-semibold">Request Write Keys</h1>

      {status === 'success' && (
        <SuggestionStatusMessage tone="success" title="Thanks!">
          We&apos;ll review your request and let you know soon!
        </SuggestionStatusMessage>
      )}
      {status === 'bad_event' && (
        <SuggestionStatusMessage tone="error" title="Event not found">
          You can only request keys for events that are already on The Blue
          Alliance. If you can&apos;t find your event,{' '}
          <a href="/suggest/offseason" className="underline underline-offset-4">
            suggest it
          </a>
          .
        </SuggestionStatusMessage>
      )}
      {status === 'no_affiliation' && (
        <SuggestionStatusMessage tone="error" title="Role required">
          Tell us your role at the event.
        </SuggestionStatusMessage>
      )}
      {(status === 'error' || status === 'unauthorized') && (
        <SuggestionStatusMessage tone="error" title="Something went wrong">
          Please try again.
        </SuggestionStatusMessage>
      )}

      <div className="space-y-2">
        <p>
          Thanks for helping make The Blue Alliance better! If you run an
          offseason event, write keys let you import its data with the{' '}
          <a href="/eventwizard2" className="underline underline-offset-4">
            Event Wizard
          </a>
          ,{' '}
          <a
            href="https://github.com/the-blue-alliance/fms-companion-dist"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-4"
          >
            FMS Companion
          </a>
          , or{' '}
          <a
            href="https://github.com/Team254/cheesy-arena"
            target="_blank"
            rel="noopener noreferrer"
            className="underline underline-offset-4"
          >
            Cheesy Arena
          </a>
          .
        </p>
        <ul className="list-disc space-y-1 pl-6 text-sm text-muted-foreground">
          <li>A moderator will review your request.</li>
          <li>
            We&apos;ll email the result to{' '}
            <strong className="text-foreground">{user.email}</strong>. Your keys
            will also appear on your{' '}
            <Link to="/account" className="underline underline-offset-4">
              account page
            </Link>
            .
          </li>
          <li>
            Keys are for offseason events. For official events, you can only
            request match video keys. To report errors in official event data,{' '}
            <Link to="/contact" className="underline underline-offset-4">
              contact us
            </Link>
            .
          </li>
          <li>
            The event must already be on The Blue Alliance. If it isn&apos;t,{' '}
            <a
              href="/suggest/offseason"
              className="underline underline-offset-4"
            >
              suggest it
            </a>{' '}
            first.
          </li>
          <li>
            You must be on the team running the event or a scoring table
            volunteer.
          </li>
        </ul>
      </div>

      <form onSubmit={(e) => handleSubmit(e)} className="space-y-4">
        <label htmlFor="event-key" className="block space-y-1">
          <span className="text-sm font-medium">Event key</span>
          <Input
            id="event-key"
            value={eventKey}
            onChange={(e) => setEventKey(e.target.value)}
            placeholder="2026cthar"
            required
          />
        </label>
        <label htmlFor="affiliation" className="block space-y-1">
          <span className="text-sm font-medium">Your role at the event</span>
          <Input
            id="affiliation"
            value={affiliation}
            onChange={(e) => setAffiliation(e.target.value)}
            placeholder="What will you be doing?"
            required
          />
        </label>
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Permissions</legend>
          <div
            className="grid grid-cols-[repeat(auto-fill,minmax(10rem,1fr))]
              gap-2"
          >
            {WRITE_TYPES.map(({ id, label }) => (
              <label key={id} className="flex items-center gap-2 text-sm">
                <Checkbox
                  checked={authTypes.includes(id)}
                  onCheckedChange={(checked) => toggleAuthType(id, checked)}
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>
        <Button type="submit" disabled={isPending}>
          {isPending ? 'Submitting…' : 'Request Keys'}
        </Button>
      </form>
    </div>
  );
}
