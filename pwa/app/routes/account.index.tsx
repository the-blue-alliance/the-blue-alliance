import { useQuery } from '@tanstack/react-query';
import { Link, createFileRoute } from '@tanstack/react-router';
import { deleteUser, updateProfile } from 'firebase/auth';
import { Mail, User } from 'lucide-react';
import { useState } from 'react';

import { listFavorites, listSubscriptions } from '~/api/tba/mobile/sdk.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
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

export const Route = createFileRoute('/account/')({
  component: Account,
});

function Account() {
  const { isInitialLoading, user, logout } = useAuth();

  const { data: favorites } = useQuery({
    queryKey: ['favorites', user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listFavorites({
        auth: token,
      });
      return response.data;
    },
    enabled: !!user,
  });

  const { data: subscriptions } = useQuery({
    queryKey: ['subscriptions', user?.uid],
    queryFn: async () => {
      if (!user) throw new Error('User not authenticated');
      const token = await user.getIdToken();
      const response = await listSubscriptions({
        auth: token,
      });
      return response.data;
    },
    enabled: !!user,
  });

  if (isInitialLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <div>
      <div className="flex flex-row items-center justify-between py-4">
        <h1 className="text-2xl font-bold">Account</h1>
        <Button variant="default" onClick={() => void logout()}>
          Logout
        </Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Manage your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-foreground">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{user.displayName}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Mail className="h-4 w-4" />
                <span className="text-sm">{user.email}</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <EditProfileDialog
              displayName={user.displayName ?? ''}
              onSave={async (newDisplayName) => {
                await updateProfile(user, { displayName: newDisplayName });
              }}
            />
            <DeleteAccountDialog
              onConfirm={async () => {
                await deleteUser(user);
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* myTBA Section */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>myTBA</CardTitle>
          <CardDescription>
            Manage your favorites and subscriptions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border bg-card p-4">
              <div className="text-2xl font-bold text-foreground">
                {favorites?.favorites?.length}
              </div>
              <div className="text-sm text-muted-foreground">Favorites</div>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <div className="text-2xl font-bold text-foreground">
                {subscriptions?.subscriptions?.length}
              </div>
              <div className="text-sm text-muted-foreground">Subscriptions</div>
            </div>
          </div>
          <Button size="sm" asChild>
            <Link to="/account/mytba">Manage myTBA</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function EditProfileDialog({
  displayName,
  onSave,
}: {
  displayName: string;
  onSave: (newDisplayName: string) => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(displayName);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Display name cannot be empty.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(name.trim());
      setOpen(false);
    } catch {
      setError('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (isOpen) {
          setName(displayName);
          setError(null);
        }
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm">Edit Profile</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
          <DialogDescription>Update your display name.</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <span className="text-sm font-medium">Display Name</span>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your display name"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={() => void handleSave()} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function DeleteAccountDialog({
  onConfirm,
}: {
  onConfirm: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await onConfirm();
      setOpen(false);
    } catch {
      setError(
        'Failed to delete account. You may need to sign in again before deleting.',
      );
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        setOpen(isOpen);
        if (isOpen) {
          setConfirmText('');
          setError(null);
        }
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm" variant="destructive">
          Delete Account
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete Account</DialogTitle>
          <DialogDescription>
            This action is permanent and cannot be undone. All your data,
            favorites, and subscriptions will be deleted.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <span className="text-sm font-medium">
              Type <strong>DELETE</strong> to confirm
            </span>
            <Input
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="DELETE"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => void handleDelete()}
            disabled={confirmText !== 'DELETE' || deleting}
          >
            {deleting ? 'Deleting...' : 'Delete Account'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
