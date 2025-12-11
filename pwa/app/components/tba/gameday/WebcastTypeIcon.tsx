import MonitorPlayIcon from '~icons/lucide/monitor-play';
import TwitchIcon from '~icons/simple-icons/twitch';
import YouTubeIcon from '~icons/simple-icons/youtube';

import type { WebcastType } from '~/lib/gameday/types';
import { cn } from '~/lib/utils';

export function WebcastTypeIcon({
  type,
  className,
}: {
  type: WebcastType;
  className?: string;
}) {
  switch (type) {
    case 'youtube':
      return <YouTubeIcon className={cn('text-red-600', className)} />;
    case 'twitch':
      return <TwitchIcon className={cn('text-purple-600', className)} />;
    default:
      return (
        <MonitorPlayIcon className={cn('text-muted-foreground', className)} />
      );
  }
}
