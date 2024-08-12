import { Link } from '@remix-run/react';
import { AwardRecipient } from '~/api/v3';

export default function AwardRecipientLink({
  recipient,
}: {
  recipient: AwardRecipient;
}) {
  const teamLink = recipient.team_key ? (
    <Link to={`/team/${recipient.team_key.substring(3)}`}>
      {recipient.team_key.substring(3)}
    </Link>
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
