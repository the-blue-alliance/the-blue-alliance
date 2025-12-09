import { ElementType } from 'react';

import EventsIcon from '~icons/lucide/calendar';
import InsightsIcon from '~icons/lucide/chart-line';
import AccountIcon from '~icons/lucide/star';
import TeamsIcon from '~icons/lucide/users-round';
import WebcastIcon from '~icons/lucide/video';

import { FileRouteTypes } from '~/routeTree.gen';

export type NavItemChild = {
  title: string;
  href?: string;
  to?: FileRouteTypes['to'];
  icon: ElementType;
};

export const NAV_ITEMS_LIST: NavItemChild[] = [
  {
    title: 'myTBA',
    to: '/account',
    icon: AccountIcon,
  },
  {
    title: 'Events',
    to: '/events/{-$year}',
    icon: EventsIcon,
  },
  {
    title: 'Teams',
    href: '/teams',
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
    icon: InsightsIcon,
  },
];
