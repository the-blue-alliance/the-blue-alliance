import { ElementType } from 'react';

import EventsIcon from '~icons/lucide/calendar';
import InsightsIcon from '~icons/lucide/chart-line';
import HomeIcon from '~icons/lucide/home';
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
    title: 'Home',
    href: '/',
    icon: HomeIcon,
  },
  {
    title: 'myTBA',
    href: '/mytba',
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
