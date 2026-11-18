import { Link } from '@tanstack/react-router';
import { useId, useState } from 'react';

import { useAuth } from '~/components/tba/auth/auth';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { useWebhooks } from '~/lib/hooks/useWebhooks';

export interface WebhookTestFormProps {
  notificationType: string;
  label: string;
  eventKey?: string;
  matchKey?: string;
}

type Result = { ok: true } | { ok: false; message: string };

export default function WebhookTestForm(props: WebhookTestFormProps) {
  const { isInitialLoading, user } = useAuth();

  return (
    <div className="mt-4 rounded-lg border p-4">
      <h4 className="mb-3 font-medium">Send a test notification</h4>
      {isInitialLoading ? null : user ? (
        <SignedInWebhookTestForm {...props} />
      ) : (
        <p className="text-sm text-muted-foreground">
          <Link to="/account">Sign in</Link> to send a test notification to your
          webhooks.
        </p>
      )}
    </div>
  );
}

function SignedInWebhookTestForm({
  notificationType,
  label,
  eventKey: defaultEventKey,
  matchKey: defaultMatchKey,
}: WebhookTestFormProps) {
  const { webhooks, isLoading, sendTest } = useWebhooks();
  const verified = webhooks.filter((w) => w.verified);
  const [eventKey, setEventKey] = useState(defaultEventKey);
  const [matchKey, setMatchKey] = useState(defaultMatchKey);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const id = useId();

  if (isLoading) return null;

  if (verified.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        You have no verified webhooks. Add or verify one on your{' '}
        <Link to="/account">account page</Link>.
      </p>
    );
  }

  const webhookId = selectedId ?? verified[0].webhook_id;
  const items = verified.map((w) => ({ value: w.webhook_id, label: w.name }));

  const send = async () => {
    setIsSending(true);
    setResult(null);
    try {
      await sendTest({
        webhook_id: webhookId,
        notification_type: notificationType,
        event_key: eventKey?.trim(),
        match_key: matchKey?.trim(),
      });
      setResult({ ok: true });
    } catch (error) {
      setResult({
        ok: false,
        message:
          error instanceof Error
            ? error.message
            : 'Failed to send test notification',
      });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <form
      className="grid gap-3 sm:grid-cols-[8rem_1fr] sm:items-center"
      onSubmit={(e) => {
        e.preventDefault();
        void send();
      }}
    >
      {eventKey !== undefined && (
        <>
          <label htmlFor={`${id}-event`} className="text-sm font-medium">
            Event key
          </label>
          <Input
            id={`${id}-event`}
            value={eventKey}
            onChange={(e) => setEventKey(e.target.value)}
            required
          />
        </>
      )}
      {matchKey !== undefined && (
        <>
          <label htmlFor={`${id}-match`} className="text-sm font-medium">
            Match key
          </label>
          <Input
            id={`${id}-match`}
            value={matchKey}
            onChange={(e) => setMatchKey(e.target.value)}
            required
          />
        </>
      )}
      <span id={`${id}-webhook`} className="text-sm font-medium">
        Send to
      </span>
      <Select
        items={items}
        value={webhookId}
        onValueChange={(value) => setSelectedId(value)}
      >
        <SelectTrigger aria-labelledby={`${id}-webhook`}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent align="start">
          {items.map(({ value, label: name }) => (
            <SelectItem key={value} value={value}>
              {name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <div className="flex flex-wrap items-center gap-3 sm:col-start-2">
        <Button type="submit" size="sm" disabled={isSending}>
          {isSending ? 'Sending...' : `Send test ${label}`}
        </Button>
        {result && (
          <output
            className={
              result.ok
                ? 'text-sm text-green-600 dark:text-green-400'
                : 'text-sm text-destructive'
            }
          >
            {result.ok ? 'Sent.' : result.message}
          </output>
        )}
      </div>
    </form>
  );
}
