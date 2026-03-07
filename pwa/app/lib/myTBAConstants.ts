import type { NotificationType } from '~/api/tba/mobile/types.gen';

export const SUBSCRIPTION_TYPE_DISPLAY_NAMES: Record<NotificationType, string> =
  {
    upcoming_match: 'Upcoming Match',
    match_score: 'Match Score',
    alliance_selection: 'Alliance Selection',
    awards_posted: 'Awards Posted',
    match_video_added: 'Match Video Added',
  };

export const SUBSCRIPTION_TYPES = Object.keys(
  SUBSCRIPTION_TYPE_DISPLAY_NAMES,
) as NotificationType[];
