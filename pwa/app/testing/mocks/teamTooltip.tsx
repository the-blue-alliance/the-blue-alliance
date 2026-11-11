import type { AnchorHTMLAttributes } from 'react';

import type { TeamTooltipProps } from '~/components/tba/teamTooltip';

export function TeamLinkWithTooltip({
  teamKey,
  year,
  disqualified: _disqualified,
  surrogate: _surrogate,
  isWinner: _isWinner,
  isCaptain: _isCaptain,
  ...props
}: TeamTooltipProps & AnchorHTMLAttributes<HTMLAnchorElement>) {
  const teamNumber = teamKey.substring(3);
  return (
    <a href={`/team/${teamNumber}/${year}`} {...props}>
      {teamNumber}
    </a>
  );
}
