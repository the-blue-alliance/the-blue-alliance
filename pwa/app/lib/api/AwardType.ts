import { AwardType, EventType } from '~/api/tba/read';

export const BLUE_BANNER_AWARDS = new Set<AwardType>([
  AwardType.CHAIRMANS,
  AwardType.CHAIRMANS_FINALIST,
  AwardType.WINNER,
  AwardType.WOODIE_FLOWERS,
  AwardType.SKILLS_COMPETITION_WINNER,
  AwardType.GAME_DESIGN_CHALLENGE_WINNER,
]);

export const INDIVIDUAL_AWARDS = new Set<AwardType>([
  AwardType.WOODIE_FLOWERS,
  AwardType.DEANS_LIST,
  AwardType.VOLUNTEER,
  AwardType.FOUNDERS,
  AwardType.BART_KAMEN_MEMORIAL,
  AwardType.MAKE_IT_LOUD,
]);

export const NON_JUDGED_NON_TEAM_AWARDS = new Set<AwardType>([
  AwardType.HIGHEST_ROOKIE_SEED,
  AwardType.WOODIE_FLOWERS,
  AwardType.DEANS_LIST,
  AwardType.VOLUNTEER,
  AwardType.WINNER,
  AwardType.FINALIST,
  AwardType.WILDCARD,
]);

export const MACHINE_AWARDS = new Set<AwardType>([
  AwardType.AUTONOMOUS,
  AwardType.CREATIVITY,
  AwardType.ENGINEERING_EXCELLENCE,
  AwardType.INDUSTRIAL_DESIGN,
  AwardType.INNOVATION_IN_CONTROL,
  AwardType.QUALITY,
]);

export const TEAM_ATTRIBUTE_AWARDS = new Set<AwardType>([
  AwardType.ENGINEERING_INSPIRATION,
  AwardType.GRACIOUS_PROFESSIONALISM,
  AwardType.IMAGERY,
  AwardType.JUDGES,
  AwardType.ROOKIE_ALL_STAR,
  AwardType.ROOKIE_INSPIRATION,
  AwardType.SPIRIT,
  AwardType.SUSTAINABILITY,
]);

export const SUBMITTED_AWARDS = new Set<AwardType>([
  AwardType.CHAIRMANS,
  AwardType.CHAIRMANS_FINALIST,
  AwardType.DEANS_LIST,
  AwardType.SAFETY,
  AwardType.WOODIE_FLOWERS,
]);

export const ROBOT_PERFORMANCE_AWARDS = new Set<AwardType>([
  AwardType.FINALIST,
  AwardType.WINNER,
]);

export const AwardCategory = {
  MACHINE_AWARDS: 1,
  TEAM_ATTRIBUTE_AWARDS: 2,
  SUBMITTED_AWARDS: 3,
  ROBOT_PERFORMANCE_AWARDS: 4,
} as const;
export type AwardCategory = (typeof AwardCategory)[keyof typeof AwardCategory];

export const SORT_ORDER: Partial<Record<AwardType, number>> = {
  [AwardType.CHAIRMANS]: 0,
  [AwardType.FOUNDERS]: 1,
  [AwardType.ENGINEERING_INSPIRATION]: 2,
  [AwardType.ROOKIE_ALL_STAR]: 3,
  [AwardType.WOODIE_FLOWERS]: 4,
  [AwardType.VOLUNTEER]: 5,
  [AwardType.DEANS_LIST]: 6,
  [AwardType.WINNER]: 7,
  [AwardType.FINALIST]: 8,
};

export function getNormalizedName(
  awardType: AwardType,
  eventType?: EventType,
  year?: number,
) {
  switch (awardType) {
    case AwardType.CHAIRMANS:
      return (year ?? 0) >= 2023 ? 'FIRST Impact Award' : "Chairman's Award";
    case AwardType.CHAIRMANS_FINALIST:
      return (year ?? 0) >= 2023
        ? 'FIRST Impact Award Finalist'
        : "Chairman's Award Finalist";
    case AwardType.WINNER:
      return 'Winner';
    case AwardType.WOODIE_FLOWERS:
      return eventType === EventType.CMP_FINALS
        ? 'Woodie Flowers Award'
        : 'Woodie Flowers Finalist Award';
    case AwardType.SKILLS_COMPETITION_WINNER:
      return 'Skills Competition Winner';
    case AwardType.GAME_DESIGN_CHALLENGE_WINNER:
      return 'Game Design Challenge Winner';
    default:
      return '';
  }
}
