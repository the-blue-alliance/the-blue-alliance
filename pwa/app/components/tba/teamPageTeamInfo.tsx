import type { ReactNode } from 'react';
import SponsorsIcon from '~icons/lucide/anchor';
import SourceIcon from '~icons/lucide/badge-check';
import StatbotIcon from '~icons/lucide/chart-spline';
import DistrictIcon from '~icons/lucide/map';
import LocationIcon from '~icons/lucide/map-pin';
import RookieIcon from '~icons/lucide/sprout';

import { District, Media, Team } from '~/api/tba/read';
import DetailEntity from '~/components/tba/detailEntity';
import { DistrictLink, TeamLocationLink } from '~/components/tba/links';
import TeamAvatar from '~/components/tba/teamAvatar';
import TeamSocialMediaList from '~/components/tba/teamSocialMediaList';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '~/components/ui/accordion';
import { Badge } from '~/components/ui/badge';
import {
  attemptToParseSchoolNameFromOldTeamName,
  attemptToParseSponsors,
} from '~/lib/teamUtils';
import { pluralize } from '~/lib/utils';

export default function TeamPageTeamInfo({
  team,
  maybeAvatar,
  socials,
  district,
  favoriteButton,
}: {
  team: Team;
  maybeAvatar: Media | undefined; // undefined on team history page
  socials: Media[];
  district?: District;
  favoriteButton?: ReactNode;
}) {
  const sponsors = attemptToParseSponsors(team.name);
  const schoolName =
    team.school_name ?? attemptToParseSchoolNameFromOldTeamName(team.name);

  return (
    <>
      <div>
        <div className="mb-2 flex items-center gap-2">
          {maybeAvatar && <TeamAvatar media={maybeAvatar} />}
          <h1 className="text-3xl font-medium">
            Team {team.team_number} - {team.nickname}
          </h1>
          {favoriteButton}
        </div>

        <div className="mb-2 space-y-1">
          <DetailEntity icon={<LocationIcon />}>
            <TeamLocationLink team={team} />
          </DetailEntity>

          {district && (
            <DetailEntity icon={<DistrictIcon />}>
              Part of the{' '}
              <DistrictLink
                districtAbbreviation={district.abbreviation}
                year={district.year}
              >
                {district.display_name}
              </DistrictLink>{' '}
              District
            </DetailEntity>
          )}

          {sponsors.length > 0 ? (
            <Accordion type="single" collapsible>
              <AccordionItem value="item-1" className="border-0">
                <AccordionTrigger className="justify-normal p-0 text-left font-normal">
                  <DetailEntity icon={<SponsorsIcon />}>
                    {schoolName}
                    {sponsors.length > 0 &&
                      ` with ${pluralize(sponsors.length, ' sponsor', ' sponsors')}`}
                  </DetailEntity>
                </AccordionTrigger>
                <AccordionContent className="pb-0">
                  {sponsors.map((sponsor, i) => (
                    <Badge
                      className="m-px font-normal"
                      key={i}
                      variant={'secondary'}
                    >
                      {sponsor}
                    </Badge>
                  ))}
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          ) : (
            <DetailEntity icon={<SponsorsIcon />}>{schoolName}</DetailEntity>
          )}

          <DetailEntity icon={<RookieIcon />}>
            Rookie Year: {team.rookie_year}
          </DetailEntity>
          <DetailEntity icon={<SourceIcon />}>
            Details on{' '}
            <a
              href={`https://frc-events.firstinspires.org/team/${team.team_number}`}
              target="_blank"
              rel="noreferrer"
            >
              FRC Events
            </a>
          </DetailEntity>
          <DetailEntity icon={<StatbotIcon />}>
            <a
              href={`https://www.statbotics.io/team/${team.team_number}`}
              target="_blank"
              rel="noreferrer"
            >
              Statbotics
            </a>
          </DetailEntity>
        </div>
      </div>

      <div className="flex flex-wrap justify-center md:justify-start">
        <TeamSocialMediaList socials={socials} />
      </div>
    </>
  );
}
