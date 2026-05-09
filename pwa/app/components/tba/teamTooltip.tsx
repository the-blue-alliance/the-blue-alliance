import { useSuspenseQuery } from '@tanstack/react-query';
import { ComponentProps, Suspense, useMemo } from 'react';

import BiTrophy from '~icons/bi/trophy';

import { MediaAvatar } from '~/api/tba/read';
import {
  getSearchIndexOptions,
  getTeamMediaByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import InlineIcon from '~/components/tba/inlineIcon';
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
  isWinner?: boolean;
  isCaptain?: boolean;
}

export function TeamLinkWithTooltip({
  teamKey,
  year,
  disqualified,
  surrogate,
  isWinner,
  isCaptain,
  ...props
}: TeamTooltipProps & Omit<ComponentProps<typeof TeamLink>, 'teamOrKey'>) {
  const teamNumber = teamKey.substring(3);

  return (
    <Tooltip delayDuration={1000}>
      <TooltipTrigger asChild>
        <TeamLink teamOrKey={teamKey} year={year} {...props}>
          {isWinner ? (
            <InlineIcon className="relative right-[1ch] justify-center">
              <BiTrophy />
              {teamNumber}
              {isCaptain && (
                <sup className="ml-[0.1em] text-[0.6em] text-muted-foreground">
                  C
                </sup>
              )}
            </InlineIcon>
          ) : isCaptain ? (
            <>
              {teamNumber}
              <sup className="ml-[0.1em] text-[0.6em] text-muted-foreground">
                C
              </sup>
            </>
          ) : (
            <>{teamNumber}</>
          )}
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

  const { data: searchIndex } = useSuspenseQuery(getSearchIndexOptions({}));

  const team = useMemo(
    () => searchIndex && searchIndex.teams.find((t) => t.key === teamKey),
    [searchIndex, teamKey],
  );

  const maybeAvatar = useMemo(
    () => media && media.find((m): m is MediaAvatar => m.type === 'avatar'),
    [media],
  );

  if (!team) return null;

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
