import { Link } from '@tanstack/react-router';
import { useId, useState } from 'react';
import { toast } from 'sonner';

import CheckIcon from '~icons/lucide/circle-check';
import TrashIcon from '~icons/lucide/trash-2';
import WebhookIcon from '~icons/lucide/webhook';

import type { Webhook } from '~/api/tba/mobile/types.gen';
import { Badge } from '~/components/ui/badge';
import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
import { Input } from '~/components/ui/input';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { useWebhooks } from '~/lib/hooks/useWebhooks';

type Webhooks = ReturnType<typeof useWebhooks>;

export default function WebhooksSection() {
  const webhooks = useWebhooks();

  return (
    <Card className="mt-4">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <WebhookIcon className="h-4 w-4" />
            Webhooks
          </CardTitle>
          <CardDescription>
            Get notifications sent to your own server. See the{' '}
            <Link to="/apidocs/webhooks">webhook docs</Link>.
          </CardDescription>
        </div>
        <AddWebhookDialog onAdd={webhooks.addWebhook} />
      </CardHeader>
      <CardContent>
        {webhooks.isLoading ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : webhooks.webhooks.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            You have no webhooks yet.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>URL</TableHead>
                <TableHead>Secret</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-0" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {webhooks.webhooks.map((webhook) => (
                <WebhookRow
                  key={webhook.webhook_id}
                  webhook={webhook}
                  actions={webhooks}
                />
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function WebhookRow({
  webhook,
  actions,
}: {
  webhook: Webhook;
  actions: Webhooks;
}) {
  const [isPinging, setIsPinging] = useState(false);
  const [isResending, setIsResending] = useState(false);

  const ping = async () => {
    setIsPinging(true);
    try {
      await actions.pingWebhook(webhook.url);
      toast.success(`Sent a ping to ${webhook.name}.`);
    } catch {
      toast.error(`Could not send a ping to ${webhook.name}.`);
    } finally {
      setIsPinging(false);
    }
  };

  const resend = async () => {
    setIsResending(true);
    try {
      await actions.resendVerification(webhook.webhook_id);
      toast.success(`Sent a new verification code to ${webhook.name}.`);
    } catch {
      toast.error(`Could not send a new code to ${webhook.name}.`);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <TableRow>
      <TableCell>{webhook.name}</TableCell>
      <TableCell className="max-w-[16rem] font-mono text-xs break-all">
        {webhook.url}
      </TableCell>
      <TableCell className="max-w-[16rem] font-mono text-xs break-all">
        {webhook.secret}
      </TableCell>
      <TableCell>
        {webhook.verified ? (
          <Badge variant="success" className="gap-1">
            <CheckIcon className="h-3 w-3" />
            Verified
          </Badge>
        ) : (
          <div className="flex flex-wrap gap-2">
            <VerifyWebhookDialog
              webhook={webhook}
              onVerify={actions.verifyWebhook}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={() => void resend()}
              disabled={isResending}
            >
              {isResending ? 'Sending...' : 'Resend Code'}
            </Button>
          </div>
        )}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1">
          <Button
            size="sm"
            variant="outline"
            onClick={() => void ping()}
            disabled={isPinging}
          >
            {isPinging ? 'Pinging...' : 'Ping'}
          </Button>
          <DeleteWebhookDialog
            webhook={webhook}
            onConfirm={() => actions.deleteWebhook(webhook.webhook_id)}
          />
        </div>
      </TableCell>
    </TableRow>
  );
}

function AddWebhookDialog({ onAdd }: { onAdd: Webhooks['addWebhook'] }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const id = useId();

  const handleAdd = async () => {
    if (!name.trim() || !url.trim()) {
      setError('Enter a name and a URL.');
      return;
    }
    setIsAdding(true);
    setError(null);
    try {
      await onAdd({ name: name.trim(), url: url.trim() });
      setOpen(false);
      toast.success(
        'Webhook added. We sent a verification code to its URL. Enter the code to verify the webhook.',
      );
    } catch {
      setError('Failed to add webhook. Please try again.');
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (isOpen) {
          setName('');
          setUrl('');
          setError(null);
        }
      }}
    >
      <DialogTrigger render={<Button size="sm" />}>Add Webhook</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Webhook</DialogTitle>
          <DialogDescription>
            We will send a verification code to this URL. The webhook gets
            notifications only after you verify it.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label htmlFor={`${id}-name`} className="text-sm font-medium">
              Name
            </label>
            <Input
              id={`${id}-name`}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. My scouting server"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor={`${id}-url`} className="text-sm font-medium">
              URL
            </label>
            <Input
              id={`${id}-url`}
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/tba-webhook"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={() => void handleAdd()} disabled={isAdding}>
            {isAdding ? 'Adding...' : 'Add Webhook'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function VerifyWebhookDialog({
  webhook,
  onVerify,
}: {
  webhook: Webhook;
  onVerify: Webhooks['verifyWebhook'];
}) {
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const id = useId();

  const handleVerify = async () => {
    if (!code.trim()) {
      setError('Enter the verification code.');
      return;
    }
    setIsVerifying(true);
    setError(null);
    try {
      await onVerify({ webhook_id: webhook.webhook_id, code: code.trim() });
      setOpen(false);
      toast.success(`${webhook.name} is verified.`);
    } catch {
      setError(
        'That code did not work. Check that it is the most recent code sent to your webhook.',
      );
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (isOpen) {
          setCode('');
          setError(null);
        }
      }}
    >
      <DialogTrigger render={<Button size="sm" />}>Verify</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Verify {webhook.name}</DialogTitle>
          <DialogDescription>
            Enter the <code>verification_key</code> from the most recent
            verification message sent to {webhook.url}.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label htmlFor={`${id}-code`} className="text-sm font-medium">
              Verification code
            </label>
            <Input
              id={`${id}-code`}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="font-mono"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={() => void handleVerify()} disabled={isVerifying}>
            {isVerifying ? 'Verifying...' : 'Verify'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DeleteWebhookDialog({
  webhook,
  onConfirm,
}: {
  webhook: Webhook;
  onConfirm: () => Promise<unknown>;
}) {
  const [open, setOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      await onConfirm();
      setOpen(false);
    } catch {
      setError('Failed to delete webhook. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (isOpen) setError(null);
      }}
    >
      <DialogTrigger
        render={
          <Button
            size="icon"
            variant="ghost"
            aria-label={`Delete ${webhook.name}`}
          />
        }
      >
        <TrashIcon className="h-4 w-4 text-destructive" />
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Webhook</DialogTitle>
          <DialogDescription>
            {webhook.name} will stop getting notifications. This cannot be
            undone.
          </DialogDescription>
        </DialogHeader>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => void handleDelete()}
            disabled={isDeleting}
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
