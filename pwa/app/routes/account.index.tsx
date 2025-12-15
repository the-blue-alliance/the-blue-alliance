import { useQuery } from '@tanstack/react-query';
import { Link, createFileRoute } from '@tanstack/react-router';
import { Mail, User } from 'lucide-react';

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
            <a href="#todo">
              <Button size="sm">Edit Profile</Button>
            </a>
            <a href="#todo">
              <Button size="sm" variant="destructive">
                Delete Account
              </Button>
            </a>
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
