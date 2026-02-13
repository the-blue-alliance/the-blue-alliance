import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import TrashIcon from '~icons/lucide/trash-2';

import { listFavorites, listSubscriptions } from '~/api/tba/mobile/sdk.gen';
import type {
  FavoriteMessage,
  ModelType,
  NotificationType,
  SubscriptionMessage,
} from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import { EventLink, TeamLink } from '~/components/tba/links';
import PreferencesDialog from '~/components/tba/preferencesDialog';
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
import { useMyTBA } from '~/lib/hooks/useMyTBA';
import {
  SUBSCRIPTION_TYPE_DISPLAY_NAMES,
  SUBSCRIPTION_TYPES,
} from '~/lib/myTBAConstants';
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

  const teamFavorites = favoritesList.filter(
    (f) => f.model_type === MODEL_TYPE.TEAM,
  );
  const teamSubscriptions = subscriptionsList.filter(
    (s) => s.model_type === MODEL_TYPE.TEAM,
  );

  const eventFavorites = favoritesList.filter(
    (f) => f.model_type === MODEL_TYPE.EVENT,
  );
  const eventSubscriptions = subscriptionsList.filter(
    (s) => s.model_type === MODEL_TYPE.EVENT,
  );

  return (
    <div>
      <div className="py-4">
        <h1 className="text-2xl font-bold">myTBA</h1>
      </div>
      <Tabs defaultValue="teams" className="mt-4">
        <TabsList>
          <TabsTrigger value="teams">My Teams</TabsTrigger>
          <TabsTrigger value="events">My Events</TabsTrigger>
        </TabsList>

        <TabsContent value="teams">
          <MyTeams
            favorites={teamFavorites}
            subscriptions={teamSubscriptions}
          />
        </TabsContent>

        <TabsContent value="events">
          <MyEvents
            favorites={eventFavorites}
            subscriptions={eventSubscriptions}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface ModelListProps {
  favorites: FavoriteMessage[];
  subscriptions: SubscriptionMessage[];
}

function buildCombinedItems(
  favorites: FavoriteMessage[],
  subscriptions: SubscriptionMessage[],
) {
  const subscriptionMap = new Map<string, Set<NotificationType>>();
  subscriptions.forEach((subscription) => {
    if (subscription.model_key) {
      subscriptionMap.set(
        subscription.model_key,
        new Set(subscription.notifications ?? []),
      );
    }
  });

  return favorites.map((f) => ({
    modelKey: f.model_key,
    modelType: f.model_type,
    notifications:
      subscriptionMap.get(f.model_key) ?? new Set<NotificationType>(),
  }));
}

function RemoveButton({
  modelKey,
  modelType,
}: {
  modelKey: string;
  modelType: ModelType;
}) {
  const { setPreferences, isPending } = useMyTBA(modelKey, modelType);

  const handleRemove = () => {
    if (window.confirm(`Remove ${modelKey} from myTBA?`)) {
      setPreferences(false, []);
    }
  };

  return (
    <Button
      size="icon"
      variant="ghost"
      onClick={handleRemove}
      disabled={isPending}
      aria-label={`Remove ${modelKey}`}
    >
      <TrashIcon className="h-4 w-4" />
    </Button>
  );
}

function MyTeams({ favorites, subscriptions }: ModelListProps) {
  const combinedItems = buildCombinedItems(favorites, subscriptions).toSorted(
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
                <TableHead>Team</TableHead>
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
                    <div className="flex items-center gap-1">
                      <PreferencesDialog
                        modelKey={item.modelKey}
                        modelType={MODEL_TYPE.TEAM}
                        trigger={
                          <Button size="sm" variant="outline">
                            Edit
                          </Button>
                        }
                      />
                      <RemoveButton
                        modelKey={item.modelKey}
                        modelType={MODEL_TYPE.TEAM}
                      />
                    </div>
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

function MyEvents({ favorites, subscriptions }: ModelListProps) {
  const combinedItems = buildCombinedItems(favorites, subscriptions).toSorted(
    (a, b) => a.modelKey.localeCompare(b.modelKey),
  );

  if (combinedItems.length === 0) {
    return (
      <Card className="mt-4">
        <CardContent className="py-8 text-center text-muted-foreground">
          No event favorites or subscriptions found
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
                <TableHead>Event</TableHead>
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
                    <EventLink
                      eventOrKey={item.modelKey}
                      className="text-primary hover:underline"
                    >
                      {item.modelKey}
                    </EventLink>
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
                    <div className="flex items-center gap-1">
                      <PreferencesDialog
                        modelKey={item.modelKey}
                        modelType={MODEL_TYPE.EVENT}
                        trigger={
                          <Button size="sm" variant="outline">
                            Edit
                          </Button>
                        }
                      />
                      <RemoveButton
                        modelKey={item.modelKey}
                        modelType={MODEL_TYPE.EVENT}
                      />
                    </div>
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
