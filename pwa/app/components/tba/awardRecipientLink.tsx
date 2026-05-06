import { AwardRecipient } from '~/api/tba/read';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';

export default function AwardRecipientLink({
  recipient,
  year,
}: {
  recipient: AwardRecipient;
  year: number;
}) {
  const teamLink = recipient.team_key ? (
    <TeamLinkWithTooltip teamKey={recipient.team_key} year={year} />
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
