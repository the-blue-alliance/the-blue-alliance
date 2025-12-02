import { Award, Event } from '~/api/tba/read';
import { EventLink } from '~/components/tba/links';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { Checkbox } from '~/components/ui/checkbox';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '~/components/ui/tooltip';
import { AwardType, BLUE_BANNER_AWARDS } from '~/lib/api/AwardType';
import { cn, pluralize } from '~/lib/utils';

interface TeamAwardsSummaryProps {
  awards: Award[];
  events: Event[];
}

interface AwardItemDefinition {
  key: string;
  label: string;
  types: AwardType[];
}

interface AwardCategoryDefinition {
  key: string;
  title: string;
  items: AwardItemDefinition[];
}

function getEventNameLookup(events: Event[]): Map<string, string> {
  const map = new Map<string, string>();

  for (const event of events) {
    const displayName =
      event.year.toString() +
      ' ' +
      (event.short_name !== null && event.short_name?.trim() !== ''
        ? event.short_name
        : event.name);

    map.set(event.key, displayName ?? event.key);
  }

  return map;
}

function getCategoryAwardCount(
  category: AwardCategoryDefinition,
  awards: Award[],
): number {
  let total = 0;

  for (const award of awards) {
    if (category.items.some((item) => item.types.includes(award.award_type))) {
      total += 1;
    }
  }

  return total;
}

const AWARD_CATEGORIES: AwardCategoryDefinition[] = [
  {
    key: 'team',
    title: 'Team awards',
    items: [
      {
        key: 'impact',
        label: 'Impact',
        types: [AwardType.CHAIRMANS, AwardType.CHAIRMANS_FINALIST],
      },
      {
        key: 'engineering-inspiration',
        label: 'Engineering Inspiration',
        types: [AwardType.ENGINEERING_INSPIRATION],
      },
      {
        key: 'gracious-professionalism',
        label: 'Gracious Professionalism',
        types: [AwardType.GRACIOUS_PROFESSIONALISM],
      },
      {
        key: 'sustainability',
        label: 'Sustainability',
        types: [AwardType.SUSTAINABILITY],
      },
      {
        key: 'imagery',
        label: 'Imagery',
        types: [AwardType.IMAGERY],
      },
    ],
  },
  {
    key: 'robot',
    title: 'Robot awards',
    items: [
      {
        key: 'creativity',
        label: 'Creativity',
        types: [AwardType.CREATIVITY],
      },
      {
        key: 'innovation-in-control',
        label: 'Innovation in Control',
        types: [AwardType.INNOVATION_IN_CONTROL],
      },
      {
        key: 'industrial-design',
        label: 'Industrial Design',
        types: [AwardType.INDUSTRIAL_DESIGN],
      },
      {
        key: 'quality',
        label: 'Quality',
        types: [AwardType.QUALITY],
      },
      {
        key: 'engineering-excellence',
        label: 'Engineering Excellence',
        types: [AwardType.ENGINEERING_EXCELLENCE],
      },
      {
        key: 'autonomous',
        label: 'Auto',
        types: [AwardType.AUTONOMOUS],
      },
    ],
  },
  {
    key: 'individual',
    title: 'Individual awards',
    items: [
      {
        key: 'deans-list',
        label: "Dean's List",
        types: [AwardType.DEANS_LIST],
      },
      {
        key: 'woodie-flowers',
        label: 'WFFA',
        types: [AwardType.WOODIE_FLOWERS],
      },
      {
        key: 'volunteer',
        label: 'Volunteer',
        types: [AwardType.VOLUNTEER],
      },
    ],
  },
  {
    key: 'performance',
    title: 'Performance',
    items: [
      {
        key: 'winner',
        label: 'Winner',
        types: [AwardType.WINNER],
      },
      {
        key: 'finalist',
        label: 'Finalist',
        types: [AwardType.FINALIST],
      },
    ],
  },
  {
    key: 'rookie',
    title: 'Rookie',
    items: [
      {
        key: 'rookie-all-star',
        label: 'Rookie All Star',
        types: [AwardType.ROOKIE_ALL_STAR],
      },
      {
        key: 'rookie-inspiration',
        label: 'Rookie Inspiration',
        types: [AwardType.ROOKIE_INSPIRATION],
      },
    ],
  },
  {
    key: 'other',
    title: 'Other',
    items: [
      {
        key: 'judges',
        label: "Judges'",
        types: [AwardType.JUDGES],
      },
      {
        key: 'spirit',
        label: 'Spirit',
        types: [AwardType.SPIRIT],
      },
    ],
  },
];

function TeamAwardsSummary({ awards, events }: TeamAwardsSummaryProps) {
  const eventNameLookup = getEventNameLookup(events);

  const blueBannerAwards = awards.filter((award) =>
    BLUE_BANNER_AWARDS.has(award.award_type),
  );

  if (awards.length === 0) {
    return null;
  }

  return (
    <section className="mt-6 space-y-4">
      <div className="flex flex-row items-baseline gap-1">
        <h2 className="text-xl font-semibold">Awards Won</h2>
        <span className="text-sm text-muted-foreground">({awards.length})</span>
        {blueBannerAwards.length > 0 && (
          <span className="text-sm text-muted-foreground">
            ({pluralize(blueBannerAwards.length, 'banner', 'banners')})
          </span>
        )}
      </div>

      <TooltipProvider>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {AWARD_CATEGORIES.map((category) => {
            const categoryCount = getCategoryAwardCount(category, awards);

            return (
              <Card key={category.key} className="border-muted shadow-none">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold">
                    {category.title}
                    {categoryCount > 0 && (
                      <span
                        className="ml-1 text-xs font-normal
                          text-muted-foreground"
                      >
                        ({categoryCount})
                      </span>
                    )}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-2">
                    {[...category.items]
                      .sort((a, b) => a.label.localeCompare(b.label))
                      .map((item: AwardItemDefinition) => {
                        const matchingAwards = awards.filter((award) =>
                          item.types.includes(award.award_type),
                        );
                        const count = matchingAwards.length;
                        const hasAward = count > 0;
                        const uniqueEventKeys = Array.from(
                          new Set(
                            matchingAwards
                              .map((award) => award.event_key)
                              .filter(
                                (eventKey) =>
                                  eventKey !== undefined &&
                                  eventKey.trim() !== '',
                              ),
                          ),
                        );

                        const content = (
                          <label
                            key={item.key}
                            className="flex items-center justify-between gap-2
                              text-sm"
                          >
                            <span className="flex items-center gap-2">
                              <Checkbox
                                checked={hasAward}
                                aria-label={item.label}
                                disabled
                              />
                              <span
                                className={cn({
                                  'font-medium': hasAward,
                                  'text-muted-foreground': !hasAward,
                                })}
                              >
                                {item.label}
                              </span>
                            </span>
                            <span
                              className="ml-2 text-xs font-medium
                                text-muted-foreground"
                            >
                              {count}
                            </span>
                          </label>
                        );

                        if (!hasAward || uniqueEventKeys.length === 0) {
                          return content;
                        }

                        return (
                          <Tooltip key={item.key}>
                            <TooltipTrigger asChild>{content}</TooltipTrigger>
                            <TooltipContent
                              side="top"
                              align="start"
                              className="max-w-xs text-xs"
                            >
                              <div className="flex flex-col gap-0.5">
                                {uniqueEventKeys.map((eventKey) => {
                                  const name =
                                    eventNameLookup.get(eventKey) ?? eventKey;

                                  return (
                                    <EventLink
                                      key={eventKey}
                                      eventOrKey={eventKey}
                                      className="underline-offset-2
                                        hover:underline"
                                    >
                                      {name}
                                    </EventLink>
                                  );
                                })}
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        );
                      })}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </TooltipProvider>
    </section>
  );
}

export default TeamAwardsSummary;
