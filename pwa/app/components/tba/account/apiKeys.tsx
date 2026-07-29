import { useState } from 'react';
import { Temporal } from 'temporal-polyfill';

import KeyIcon from '~icons/lucide/key';
import TrashIcon from '~icons/lucide/trash-2';

import type {
  ApiReadKeyMessage,
  ApiWriteKeyMessage,
} from '~/api/tba/mobile/types.gen';
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
import { useApiKeys } from '~/lib/hooks/useApiKeys';

const REQUEST_APIWRITE_URL = 'https://www.thebluealliance.com/request/apiwrite';

function formatIsoDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  try {
    return Temporal.PlainDateTime.from(iso).toPlainDate().toString();
  } catch {
    return iso;
  }
}

export default function ApiKeysSection() {
  const {
    readKeys,
    writeKeys,
    isLoading,
    addReadKey,
    isAdding,
    deleteReadKey,
    isDeleting,
  } = useApiKeys();

  return (
    <>
      <Card className="mt-4">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <KeyIcon className="h-4 w-4" />
              Read API Keys
            </CardTitle>
            <CardDescription>
              Keys for reading data from the TBA API v3
            </CardDescription>
          </div>
          <AddReadKeyDialog onAdd={addReadKey} isAdding={isAdding} />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : readKeys.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              You have no read API keys yet.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>X-TBA-Auth-Key</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="w-0" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {readKeys.map((key) => (
                  <ReadKeyRow
                    key={key.key}
                    readKey={key}
                    onDelete={deleteReadKey}
                    isDeleting={isDeleting}
                  />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <KeyIcon className="h-4 w-4" />
              Write API Keys
            </CardTitle>
            <CardDescription>
              Keys for writing event data. Granted on request.
            </CardDescription>
          </div>
          <Button
            size="sm"
            render={<a href={REQUEST_APIWRITE_URL}>Request Write Key</a>}
          />
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : writeKeys.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              You have no write API keys.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event(s)</TableHead>
                  <TableHead>Permissions</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead>Auth ID</TableHead>
                  <TableHead>Auth Secret</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {writeKeys.map((key) => (
                  <WriteKeyRow key={key.auth_id} writeKey={key} />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}

function ReadKeyRow({
  readKey,
  onDelete,
  isDeleting,
}: {
  readKey: ApiReadKeyMessage;
  onDelete: (keyId: string) => Promise<unknown>;
  isDeleting: boolean;
}) {
  return (
    <TableRow>
      <TableCell className="max-w-[16rem] font-mono text-xs break-all">
        {readKey.key}
      </TableCell>
      <TableCell className="whitespace-nowrap">
        {formatIsoDate(readKey.created)}
      </TableCell>
      <TableCell>{readKey.description}</TableCell>
      <TableCell>
        <DeleteReadKeyDialog
          description={readKey.description}
          onConfirm={() => onDelete(readKey.key)}
          isDeleting={isDeleting}
        />
      </TableCell>
    </TableRow>
  );
}

function WriteKeyRow({ writeKey }: { writeKey: ApiWriteKeyMessage }) {
  return (
    <TableRow>
      <TableCell className="whitespace-nowrap">
        {writeKey.event_keys.join(', ') || '—'}
      </TableCell>
      <TableCell>{writeKey.auth_types.join(', ')}</TableCell>
      <TableCell className="whitespace-nowrap">
        {formatIsoDate(writeKey.expiration)}
      </TableCell>
      <TableCell className="font-mono text-xs break-all">
        {writeKey.auth_id}
      </TableCell>
      <TableCell className="max-w-[16rem] font-mono text-xs break-all">
        {writeKey.secret}
      </TableCell>
    </TableRow>
  );
}

function AddReadKeyDialog({
  onAdd,
  isAdding,
}: {
  onAdd: (description: string) => Promise<unknown>;
  isAdding: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleAdd = async () => {
    if (!description.trim()) {
      setError('A description is required.');
      return;
    }
    setError(null);
    try {
      await onAdd(description.trim());
      setOpen(false);
    } catch {
      setError('Failed to add key. Please try again.');
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (isOpen) {
          setDescription('');
          setError(null);
        }
      }}
    >
      <DialogTrigger render={<Button size="sm" />}>Add Read Key</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Read API Key</DialogTitle>
          <DialogDescription>
            Give your key a description so you can remember what it is for.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <span className="text-sm font-medium">Description</span>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. My scouting app"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={() => void handleAdd()} disabled={isAdding}>
            {isAdding ? 'Adding...' : 'Add Key'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DeleteReadKeyDialog({
  description,
  onConfirm,
  isDeleting,
}: {
  description: string;
  onConfirm: () => Promise<unknown>;
  isDeleting: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setError(null);
    try {
      await onConfirm();
      setOpen(false);
    } catch {
      setError('Failed to delete key. Please try again.');
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
        render={<Button size="icon" variant="ghost" aria-label="Delete key" />}
      >
        <TrashIcon className="h-4 w-4 text-destructive" />
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Read API Key</DialogTitle>
          <DialogDescription>
            This will permanently revoke the key
            {description ? ` "${description}"` : ''}. Any apps using it will
            stop working.
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
