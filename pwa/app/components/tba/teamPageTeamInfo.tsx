import { Link } from 'react-router';

import BiCalendar from '~icons/bi/calendar';
import BiGraphUp from '~icons/bi/graph-up';
import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiLink from '~icons/bi/link';
import BiPinMapFill from '~icons/bi/pin-map-fill';

import { Media, Team } from '~/api/v3';
import InlineIcon from '~/components/tba/inlineIcon';
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
        <h1 className="mb-2.5 text-4xl">
          {maybeAvatar && <TeamAvatar media={maybeAvatar} />}
          Team {team.team_number} - {team.nickname}
        </h1>
        <InlineIcon>
          <BiPinMapFill />
          <a
            href={`https://maps.google.com/maps?q=${team.city}, ${team.state_prov}, ${team.country}`}
          >
            {team.city}, {team.state_prov}, {team.country}
          </a>
        </InlineIcon>

        {sponsors.length > 0 ? (
          <Accordion type="single" collapsible>
            <AccordionItem value="item-1" className="border-0">
              <AccordionTrigger className="justify-normal p-0 text-left font-normal">
                <InlineIcon displayStyle={'flexless'}>
                  <BiInfoCircleFill />
                  {schoolName}
                  {sponsors.length > 0 &&
                    ` with ${pluralize(sponsors.length, ' sponsor', ' sponsors')}`}
                </InlineIcon>
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
          <InlineIcon displayStyle={'flexless'}>
            <BiInfoCircleFill />
            {schoolName}
          </InlineIcon>
        )}

        <InlineIcon>
          <BiCalendar />
          Rookie Year: {team.rookie_year}
        </InlineIcon>

        <InlineIcon>
          <BiLink />
          Details on{' '}
          <Link
            to={`https://frc-events.firstinspires.org/team/${team.team_number}`}
          >
            FRC Events
          </Link>
        </InlineIcon>

        <InlineIcon>
          <BiGraphUp />
          <Link to={`https://www.statbotics.io/team/${team.team_number}`}>
            Statbotics
          </Link>
        </InlineIcon>
      </div>

      <div className="flex flex-wrap justify-center md:justify-start">
        <TeamSocialMediaList socials={socials} />
      </div>
    </>
  );
}
