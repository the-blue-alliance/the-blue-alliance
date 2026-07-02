import TeamListTable from '~/components/tba/teamListTable';
import { Separator } from '~/components/ui/separator';
import { useFavoriteTeams } from '~/lib/hooks/useFavoriteTeams';

export default function FavoriteTeamsSection() {
  const { favoriteTeams, isLoading } = useFavoriteTeams();

  if (isLoading || favoriteTeams.length === 0) {
    return null;
  }

  return (
    <>
      <h1 className="mb-3 text-3xl font-medium">Favorite Teams</h1>
      <TeamListTable teams={favoriteTeams} />
      <Separator className="my-6" />
    </>
  );
}
