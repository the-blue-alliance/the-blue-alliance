import { Link } from '@remix-run/react';

import BiBarChartLineFill from '~icons/bi/bar-chart-line-fill';
import BiCameraVideoFill from '~icons/bi/camera-video-fill';
import BiGearFill from '~icons/bi/gear-fill';
import BiPencilFill from '~icons/bi/pencil-fill';
import BiPeopleFill from '~icons/bi/people-fill';
import BiStarFill from '~icons/bi/star-fill';
import BiThreeDotsVertical from '~icons/bi/three-dots-vertical';
import IonCalendar from '~icons/ion/calendar';

import { Input } from '~/components/ui/input';
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from '~/components/ui/navigation-menu';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import lamp from '~/images/tba/tba-lamp.svg';
import { cn } from '~/lib/utils';

import GlobalLoadingProgress from './globalLoadingProgress';

interface MenuItemProps {
  route?: string;
  icon: React.ReactNode;
  title: string;
}

export const MenuItem = ({ icon, title, route }: MenuItemProps) => {
  return (
    <NavigationMenuItem>
      <NavigationMenuLink
        className={navigationMenuTriggerStyle() + ' h-10 px-4 cursor-pointer'}
        asChild
      >
        {route ? (
          <Link to={route} className="hover:no-underline">
            {icon}
            <div className="pl-2">{title}</div>
          </Link>
        ) : (
          <div>
            {icon}
            <div className="pl-2">{title}</div>
          </div>
        )}
      </NavigationMenuLink>
    </NavigationMenuItem>
  );
};

export const DropMenuItem = ({ icon, title }: MenuItemProps) => {
  return (
    <NavigationMenuItem
      className={cn(
        `relative flex cursor-default select-none bg-primary items-center rounded-sm
          text-md outline-none transition-colors focus:bg-background
          focus:text-accent-foreground data-[disabled]:pointer-events-none
          data-[disabled]:opacity-50`,
      )}
    >
      <NavigationMenuLink
        className={
          navigationMenuTriggerStyle() + ' cursor-pointer w-full grow h-10'
        }
      >
        <div className="flex grow flex-row flex-wrap content-between items-center justify-start px-2">
          {icon}
          <div className="pl-2 antialiased">{title}</div>
        </div>
      </NavigationMenuLink>
    </NavigationMenuItem>
  );
};

export const Nav = () => {
  return (
    <div className="fixed z-10 flex w-full grow justify-center bg-primary p-2 shadow-md">
      <GlobalLoadingProgress />
      <NavigationMenu>
        <NavigationMenuList className="flex w-full grow">
          <img
            src={lamp}
            className="size-8 pr-4"
            alt="The Blue Alliance Logo"
          />
          <Link to="/" className="hover:no-underline">
            <div className="whitespace-nowrap pr-2 text-2xl text-white">
              The Blue Alliance
            </div>
          </Link>
          <div className="grow" />
          <MenuItem icon={<BiStarFill />} title="myTBA" />
          <MenuItem icon={<IonCalendar />} title="Events" route="/events" />
          <MenuItem icon={<BiPeopleFill />} title="Teams" />
          <MenuItem icon={<BiCameraVideoFill />} title="GameDay" />
          <MenuItem
            icon={<BiBarChartLineFill />}
            title="Insights"
            route="/insights"
          />
          <Popover>
            <PopoverTrigger>
              <MenuItem title="More" icon={<BiThreeDotsVertical />} />{' '}
            </PopoverTrigger>
            <PopoverContent
              sideOffset={12}
              alignOffset={-2}
              align="start"
              className={cn(
                `mt-6 bg-primary px-1 py-1 w-30 m-0 border-none drop-shadow-lg shadow-l
                  rounded-md `,
              )}
            >
              <DropMenuItem icon={<BiPencilFill />} title="Blog" />
              <DropMenuItem icon={<BiGearFill />} title="Account" />
            </PopoverContent>
          </Popover>
        </NavigationMenuList>
        <Input
          placeholder="Search"
          type="search"
          className="focus:ring-none ml-8 h-8 border-none bg-accent transition-all
              focus:bg-white focus:text-black focus:outline-none focus-visible:border-none"
        />
      </NavigationMenu>
    </div>
  );
};
