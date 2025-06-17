import { AwardRecipient } from '~/api/tba';
import { TeamLink } from '~/components/tba/links';

export default function AwardRecipientLink({
  recipient,
  year,
}: {
  recipient: AwardRecipient;
  year?: number;
}) {
  const teamLink = recipient.team_key ? (
    <TeamLink teamOrKey={recipient.team_key} year={year}>
      {recipient.team_key.substring(3)}
    </TeamLink>
  ) : (
    <></>
  );

  if (recipient.awardee) {
    if (recipient.team_key) {
      return (
        <>
          {recipient.awardee} ({teamLink})
        </>
      );
    }

    return <>{recipient.awardee}</>;
  }

  if (recipient.team_key) {
    return teamLink;
  }

  return <>n/a</>;
}
