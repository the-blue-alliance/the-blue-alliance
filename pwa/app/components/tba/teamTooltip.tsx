import { useSuspenseQuery } from '@tanstack/react-query';
import { ComponentProps, Suspense, useMemo } from 'react';

import { MediaAvatar } from '~/api/tba/read';
import {
  getTeamMediaByYearOptions,
  getTeamOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { TeamLink } from '~/components/tba/links';
import TeamAvatar from '~/components/tba/teamAvatar';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '~/components/ui/tooltip';

export interface TeamTooltipProps {
  teamKey: string;
  year: number;
  disqualified?: boolean;
  surrogate?: boolean;
}

export function TeamLinkWithTooltip({
  teamKey,
  year,
  disqualified,
  surrogate,
  ...props
}: TeamTooltipProps & Omit<ComponentProps<typeof TeamLink>, 'teamOrKey'>) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <TeamLink teamOrKey={teamKey} year={year} {...props}>
          {teamKey.substring(3)}
        </TeamLink>
      </TooltipTrigger>
      <Suspense>
        <TooltipContent>
          <TeamTooltip
            teamKey={teamKey}
            year={year}
            disqualified={disqualified ?? false}
            surrogate={surrogate ?? false}
          />
        </TooltipContent>
      </Suspense>
    </Tooltip>
  );
}

export function TeamTooltip({
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
