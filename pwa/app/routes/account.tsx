import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';

import { listFavorites } from '~/api/tba/mobile/sdk.gen';
import { useAuth } from '~/components/tba/auth/auth';
import LoginPage from '~/components/tba/auth/loginPage';
import { Button } from '~/components/ui/button';

export const Route = createFileRoute('/account')({
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

  if (isInitialLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <div>
      <p>Hello {user.displayName}!</p>
      <Button variant="outline" onClick={() => void logout()}>
        Logout
      </Button>

      <div className="mt-4">
        <h2 className="text-xl font-bold">Your Favorites</h2>
        {favorites ? (
          <ul>
            {favorites.favorites?.map((favorite, index) => (
              <li key={index}>
                {favorite.model_type}: {favorite.model_key}
              </li>
            ))}
          </ul>
        ) : (
          <p>Loading favorites...</p>
        )}
      </div>
    </div>
  );
}
