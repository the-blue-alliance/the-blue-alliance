import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import { listFavorites, listSubscriptions } from '~/api/tba/mobile/sdk.gen';
import type {
  FavoriteMessage,
  NotificationType,
  SubscriptionMessage,
} from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import { TeamLink } from '~/components/tba/links';
import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { MODEL_TYPE, pluralize } from '~/lib/utils';

export const Route = createFileRoute('/account/mytba')({
  component: MyTBA,
});

function MyTBA() {
  const { isInitialLoading, user } = useAuth();

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

  const favoritesList = favorites?.favorites ?? [];
  const subscriptionsList = subscriptions?.subscriptions ?? [];

  // Filter by model type
  const teamFavorites = favoritesList.filter(
    (f) => f.model_type === MODEL_TYPE.TEAM,
  );
  const teamSubscriptions = subscriptionsList.filter(
    (s) => s.model_type === MODEL_TYPE.TEAM,
  );

  return (
    <div>
      <div className="py-4">
        <h1 className="text-2xl font-bold">myTBA</h1>
      </div>
      <Tabs defaultValue="teams" className="mt-4">
        <TabsList className="flex h-auto flex-wrap items-center justify-evenly">
          <TabsTrigger value="teams">My Teams</TabsTrigger>
          <TabsTrigger value="events">My Events</TabsTrigger>
          <TabsTrigger value="matches">My Matches</TabsTrigger>
          <TabsTrigger value="attendance">My Attendance</TabsTrigger>
        </TabsList>

        <TabsContent value="teams">
          <MyTeams
            favorites={teamFavorites}
            subscriptions={teamSubscriptions}
          />
        </TabsContent>

        <TabsContent value="events">
          <MyEvents />
        </TabsContent>

        <TabsContent value="matches">
          <MyMatches />
        </TabsContent>

        <TabsContent value="attendance">
          <MyAttendance />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface MyTeamsProps {
  favorites: FavoriteMessage[];
  subscriptions: SubscriptionMessage[];
}

const SUBSCRIPTION_TYPE_DISPLAY_NAMES: Record<NotificationType, string> = {
  upcoming_match: 'Upcoming Match',
  match_score: 'Match Score',
  alliance_selection: 'Alliance Selection',
  awards_posted: 'Awards Posted',
  match_video_added: 'Match Video Added',
};

const SUBSCRIPTION_TYPES = Object.keys(
  SUBSCRIPTION_TYPE_DISPLAY_NAMES,
) as NotificationType[];

function MyTeams({ favorites, subscriptions }: MyTeamsProps) {
  const subscriptionMap = new Map<string, Set<NotificationType>>();
  subscriptions.forEach((subscription) => {
    if (subscription.model_key) {
      subscriptionMap.set(
        subscription.model_key,
        new Set(subscription.notifications ?? []),
      );
    }
  });

  const combinedItems = favorites
    .map((f) => ({
      modelKey: f.model_key,
      notifications:
        subscriptionMap.get(f.model_key) ?? new Set<NotificationType>(),
    }))
    .toSorted(
      (a, b) =>
        Number(a.modelKey.substring(3)) - Number(b.modelKey.substring(3)),
    );

  if (combinedItems.length === 0) {
    return (
      <Card className="mt-4">
        <CardContent className="py-8 text-center text-muted-foreground">
          No favorites or subscriptions found
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>Favorites & Subscriptions</CardTitle>
        <CardDescription>
          {pluralize(favorites.length, 'favorite', 'favorites')},{' '}
          {pluralize(subscriptions.length, 'subscription', 'subscriptions')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Key</TableHead>
                {SUBSCRIPTION_TYPES.map((type) => (
                  <TableHead key={type} className="text-center">
                    {SUBSCRIPTION_TYPE_DISPLAY_NAMES[type]}
                  </TableHead>
                ))}
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {combinedItems.map((item) => (
                <TableRow key={item.modelKey}>
                  <TableCell>
                    <TeamLink
                      teamOrKey={item.modelKey}
                      className="text-primary hover:underline"
                    >
                      {item.modelKey.substring(3)}
                    </TeamLink>
                  </TableCell>
                  {SUBSCRIPTION_TYPES.map((type) => (
                    <TableCell key={type} className="text-center">
                      {item.notifications.has(type) ? (
                        <span className="text-muted-foreground">✓</span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  ))}
                  <TableCell>
                    <Button size="sm" variant="outline">
                      Edit
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

function MyEvents() {
  return (
    <Card className="mt-4">
      <CardContent className="py-8 text-center text-muted-foreground">
        Coming soon
      </CardContent>
    </Card>
  );
}

function MyMatches() {
  return (
    <Card className="mt-4">
      <CardContent className="py-8 text-center text-muted-foreground">
        Coming soon
      </CardContent>
    </Card>
  );
}

function MyAttendance() {
  return (
    <Card className="mt-4">
      <CardContent className="py-8 text-center text-muted-foreground">
        Coming soon
      </CardContent>
    </Card>
  );
}
