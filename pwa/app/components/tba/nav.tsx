import { Link } from '@remix-run/react';

import BiBarChartLineFill from '~icons/bi/bar-chart-line-fill';
import BiCameraVideoFill from '~icons/bi/camera-video-fill';
import BiGearFill from '~icons/bi/gear-fill';
import BiPencilFill from '~icons/bi/pencil-fill';
import BiPeopleFill from '~icons/bi/people-fill';
import BiStarFill from '~icons/bi/star-fill';
import BiThreeDotsVertical from '~icons/bi/three-dots-vertical';
import IonCalendar from '~icons/ion/calendar';
import SearchIcon from '~icons/lucide/search';

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
  className?: string;
  route?: string;
  icon: React.ReactNode;
  title: string;
}

export const MenuItem = ({ className, icon, title, route }: MenuItemProps) => {
  return (
    <NavigationMenuItem className={className}>
      <NavigationMenuLink
        className={navigationMenuTriggerStyle() + ' cursor-pointer'}
        asChild
      >
        {route ? (
          <Link to={route} className="hover:no-underline">
            {icon}
            <div className="hidden pl-2 sm:block">{title}</div>
          </Link>
        ) : (
          <div>
            {icon}
            <div className="hidden pl-2 sm:block">{title}</div>
          </div>
        )}
      </NavigationMenuLink>
    </NavigationMenuItem>
  );
};

export const DropMenuItem = ({
  className,
  icon,
  title,
  route,
}: MenuItemProps) => {
  return (
    <NavigationMenuItem
      className={cn(
        `relative flex cursor-default select-none bg-primary items-center rounded-sm
          text-md outline-none transition-colors focus:bg-background
          focus:text-accent-foreground data-[disabled]:pointer-events-none
          data-[disabled]:opacity-50`,
        className,
      )}
    >
      <NavigationMenuLink
        className={
          navigationMenuTriggerStyle() +
          ' cursor-pointer w-full grow hover:no-underline'
        }
        asChild
      >
        {route ? (
          <Link
            to={route}
            className="flex grow flex-row flex-wrap content-between items-center justify-start px-2 text-white hover:no-underline"
          >
            {icon}
            <div className="pl-2 antialiased">{title}</div>
          </Link>
        ) : (
          <div className="flex grow flex-row flex-wrap content-between items-center justify-start px-2">
            {icon}
            <div className="pl-2 antialiased">{title}</div>
          </div>
        )}
      </NavigationMenuLink>
    </NavigationMenuItem>
  );
};

export const Nav = () => {
  return (
    <div className="fixed z-10 flex w-full grow justify-center bg-primary shadow-md">
      <GlobalLoadingProgress />
      <NavigationMenu className="px-4 py-2.5 gap-6">
        <Link to="/" className="flex items-center gap-3 hover:no-underline">
          <img
            src={lamp}
            className="size-6 max-w-none"
            alt="The Blue Alliance Logo"
          />
          <div className="hidden whitespace-nowrap text-xl font-medium tracking-tight	 text-white lg:block">
            The Blue Alliance
          </div>
        </Link>
        <NavigationMenuList className="flex w-full grow">
          <MenuItem icon={<BiStarFill />} title="myTBA" />
          <MenuItem icon={<IonCalendar />} title="Events" route="/events" />
          <MenuItem
            className="hidden md:block"
            icon={<BiPeopleFill />}
            title="Teams"
          />
          <MenuItem
            className="hidden md:block"
            icon={<BiCameraVideoFill />}
            title="GameDay"
          />
          <MenuItem
            className="hidden md:block"
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
              <DropMenuItem
                className="lg:hidden"
                icon={<BiPeopleFill />}
                title="Teams"
                route="/teams"
              />
              <DropMenuItem
                className="lg:hidden"
                icon={<BiCameraVideoFill />}
                title="GameDay"
              />
              <DropMenuItem
                className="lg:hidden"
                icon={<BiBarChartLineFill />}
                title="Insights"
                route="/insights"
              />
              <DropMenuItem icon={<BiPencilFill />} title="Blog" />
              <DropMenuItem icon={<BiGearFill />} title="Account" />
            </PopoverContent>
          </Popover>
        </NavigationMenuList>
        <div className="ml-auto">
          <form>
            <div className="relative">
              <div className="absolute left-0 inset-y-0 pl-3 flex items-center">
                <SearchIcon className="h-4 w-4 text-neutral-500" />
              </div>
              <Input
                placeholder="Search"
                className="text-sm pl-9 bg-accent transition-all hover:bg-white focus:bg-white"
              />
            </div>
          </form>
        </div>
      </NavigationMenu>
    </div>
  );
};
