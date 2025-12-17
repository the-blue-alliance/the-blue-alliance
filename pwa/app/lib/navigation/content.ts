import { LinkOptions } from '@tanstack/react-router';
import { ElementType } from 'react';

import EventsIcon from '~icons/lucide/calendar';
import InsightsIcon from '~icons/lucide/chart-line';
import myTBAIcon from '~icons/lucide/star';
import TeamsIcon from '~icons/lucide/users-round';
import WebcastIcon from '~icons/lucide/video';

type NavItemChild = {
  title: string;
  icon: ElementType;
} & Pick<LinkOptions, 'to' | 'params'>;

export const NAV_ITEMS_LIST: NavItemChild[] = [
  {
    title: 'myTBA',
    to: '/account',
    icon: myTBAIcon,
  },
  {
    title: 'Events',
    to: '/events/{-$year}',
    params: { year: undefined },
    icon: EventsIcon,
  },
  {
    title: 'Teams',
    to: '/teams/{-$pgNum}',
    params: { pgNum: undefined },
    icon: TeamsIcon,
  },
  {
    title: 'GameDay',
    to: '/gameday',
    icon: WebcastIcon,
  },
  {
    title: 'Insights',
    to: '/insights/{-$year}',
    params: { year: undefined },
    icon: InsightsIcon,
  },
];
