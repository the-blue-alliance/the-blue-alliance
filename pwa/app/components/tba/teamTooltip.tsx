import { useSuspenseQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { MediaAvatar } from '~/api/tba/read';
import {
  getTeamMediaByYearOptions,
  getTeamOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';

import TeamAvatar from '~/components/tba/teamAvatar';

export interface TeamTooltipProps {
  teamKey: string;
  year: number;
  disqualified?: boolean;
  surrogate?: boolean;
}

export default function TeamTooltip({
  teamKey,
  year,
  disqualified,
  surrogate,
}: TeamTooltipProps) {
  const { data: media } = useSuspenseQuery(
    getTeamMediaByYearOptions({ path: { team_key: teamKey, year } }),
  );

  const { data: team } = useSuspenseQuery(
    getTeamOptions({ path: { team_key: teamKey } }),
  );

  const maybeAvatar = useMemo(
    () => media && media.find((m): m is MediaAvatar => m.type === 'avatar'),
    [media],
  );

  return (
    <div>
      {maybeAvatar && <TeamAvatar media={maybeAvatar} />}
      <h1>{team.nickname}</h1>
      {disqualified && (
        <i>
          <h1>Disqualified</h1>
        </i>
      )}
      {surrogate && (
        <i>
          <h1>Surrogate</h1>
        </i>
      )}
    </div>
  );
}
