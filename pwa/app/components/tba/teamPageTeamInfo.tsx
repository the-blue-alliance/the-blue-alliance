import SponsorsIcon from '~icons/lucide/anchor';
import SourceIcon from '~icons/lucide/badge-check';
import StatbotIcon from '~icons/lucide/chart-spline';
import LocationIcon from '~icons/lucide/map-pin';
import RookieIcon from '~icons/lucide/sprout';

import { Media, Team } from '~/api/tba/read';
import DetailEntity from '~/components/tba/detailEntity';
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
}: {
  team: Team;
  maybeAvatar: Media | undefined; // undefined on team history page
  socials: Media[];
}) {
  const sponsors = attemptToParseSponsors(team.name);
  const schoolName =
    team.school_name ?? attemptToParseSchoolNameFromOldTeamName(team.name);

  return (
    <>
      <div>
        <h1 className="mb-2 text-3xl font-medium">
          {maybeAvatar && <TeamAvatar media={maybeAvatar} className="mr-3" />}
          Team {team.team_number} - {team.nickname}
        </h1>

        <div className="mb-2 space-y-1">
          <DetailEntity icon={<LocationIcon />}>
            <a
              href={`https://maps.google.com/maps?q=${team.city}, ${team.state_prov}, ${team.country}`}
            >
              {team.city}, {team.state_prov}, {team.country}
            </a>
          </DetailEntity>

          {sponsors.length > 0 ? (
            <Accordion type="single" collapsible>
              <AccordionItem value="item-1" className="border-0">
                <AccordionTrigger
                  className="justify-normal p-0 text-left font-normal"
                >
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
