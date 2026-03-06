import { match } from 'ts-pattern';

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
  const [Icon, colorClass] = match(type)
    .with('youtube', () => [YouTubeIcon, 'text-red-600'] as const)
    .with('twitch', () => [TwitchIcon, 'text-purple-600'] as const)
    .otherwise(() => [MonitorPlayIcon, 'text-muted-foreground'] as const);

  return <Icon className={cn(colorClass, className)} />;
}
