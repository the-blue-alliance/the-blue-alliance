import MatchDetails from '~/components/tba/match/matchDetails';
import {
  Credenza,
  CredenzaBody,
  CredenzaContent,
  CredenzaDescription,
  CredenzaHeader,
  CredenzaTitle,
} from '~/components/ui/credenza';
import { PlayoffType } from '~/lib/api/PlayoffType';
import { useMatchModal } from '~/lib/matchModalContext';
import { matchTitleShort } from '~/lib/matchUtils';

export default function MatchModal() {
  const { state, closeMatch } = useMatchModal();
  if (!state) {
    return null;
  }

  const { match, event } = state;
  const playoffType = event.playoff_type ?? PlayoffType.CUSTOM;
  const matchTitle = matchTitleShort(match, playoffType);

  return (
    <Credenza open={true} onOpenChange={(open) => !open && closeMatch()}>
      <CredenzaContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <CredenzaHeader>
          <CredenzaTitle>{matchTitle}</CredenzaTitle>
          <CredenzaDescription>
            {event.name} {event.year}
          </CredenzaDescription>
        </CredenzaHeader>
        <CredenzaBody className="pb-6">
          <MatchDetails match={match} event={event} />
        </CredenzaBody>
      </CredenzaContent>
    </Credenza>
  );
}
