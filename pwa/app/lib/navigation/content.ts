import { ElementType } from 'react';

import EventsIcon from '~icons/lucide/calendar';
import InsightsIcon from '~icons/lucide/chart-line';
import AccountIcon from '~icons/lucide/star';
import TeamsIcon from '~icons/lucide/users-round';
import WebcastIcon from '~icons/lucide/video';

export type NavItemChild = {
  title: string;
  href: string;
  icon: ElementType;
};

export const NAV_ITEMS_LIST: NavItemChild[] = [
  {
    title: 'myTBA',
    href: '/account',
    icon: AccountIcon,
  },
  {
    title: 'Events',
    href: '/events/{-$year}',
    icon: EventsIcon,
  },
  {
    title: 'Teams',
    href: '/teams',
    icon: TeamsIcon,
  },
  {
    title: 'GameDay',
    href: '/gameday',
    icon: WebcastIcon,
  },
  {
    title: 'Insights',
    href: '/insights/{-$year}',
    icon: InsightsIcon,
  },
];
