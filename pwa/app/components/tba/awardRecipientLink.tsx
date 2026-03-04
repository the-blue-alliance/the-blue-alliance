import { P, match } from 'ts-pattern';

import { AwardRecipient } from '~/api/tba/read';
import { TeamLink } from '~/components/tba/links';

export default function AwardRecipientLink({
  recipient,
  year,
}: {
  recipient: AwardRecipient;
  year?: number;
}) {
  return match([recipient.awardee, recipient.team_key])
    .with([P.string, P.string], ([awardee, teamKey]) => (
      <>
        {awardee} (
        <TeamLink teamOrKey={teamKey} year={year}>
          {teamKey.substring(3)}
        </TeamLink>
        )
      </>
    ))
    .with([P.string, P.nullish], ([awardee]) => <>{awardee}</>)
    .with([P.nullish, P.string], ([, teamKey]) => (
      <TeamLink teamOrKey={teamKey} year={year}>
        {teamKey.substring(3)}
      </TeamLink>
    ))
    .otherwise(() => <>n/a</>);
}
