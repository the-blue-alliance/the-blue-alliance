import type { NotificationType } from '~/api/tba/mobile/types.gen';

export const SUBSCRIPTION_TYPE_DISPLAY_NAMES: Record<NotificationType, string> =
  {
    upcoming_match: 'Upcoming Match',
    match_score: 'Match Score',
    starting_comp_level: 'Competition Level Starting',
    alliance_selection: 'Alliance Selection',
    awards_posted: 'Awards Posted',
    schedule_updated: 'Event Schedule Updated',
    match_video: 'Match Video Added',
  };

export const SUBSCRIPTION_TYPES = Object.keys(
  SUBSCRIPTION_TYPE_DISPLAY_NAMES,
) as NotificationType[];
