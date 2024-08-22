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
  className?: string;
  route?: string;
  icon: React.ReactNode;
  title: string;
}

export const MenuItem = ({ className, icon, title, route }: MenuItemProps) => {
  return (
    <NavigationMenuItem className={className}>
      <NavigationMenuLink
        className={navigationMenuTriggerStyle() + ' h-10 px-4 cursor-pointer'}
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
          ' cursor-pointer w-full grow h-10 hover:no-underline'
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
    <div className="fixed z-10 flex w-full grow justify-center bg-primary p-2 shadow-md">
      <GlobalLoadingProgress />
      <NavigationMenu>
        <NavigationMenuList className="flex w-full grow">
          <Link to="/" className="ml-4 flex hover:no-underline">
            <img
              src={lamp}
              className="size-8 max-w-none"
              alt="The Blue Alliance Logo"
            />
            <div className="ml-4 hidden whitespace-nowrap text-2xl text-white xl:block">
              The Blue Alliance
            </div>
          </Link>
          <div className="grow" />
          <MenuItem icon={<BiStarFill />} title="myTBA" />
          <MenuItem icon={<IonCalendar />} title="Events" route="/events" />
          <MenuItem
            className="hidden lg:block"
            icon={<BiPeopleFill />}
            title="Teams"
          />
          <MenuItem
            className="hidden lg:block"
            icon={<BiCameraVideoFill />}
            title="GameDay"
          />
          <MenuItem
            className="hidden lg:block"
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
        <Input
          placeholder="Search"
          type="search"
          className="focus:ring-none ml-4 h-8 border-none bg-accent transition-all
              focus:bg-white focus:text-black focus:outline-none focus-visible:border-none"
        />
      </NavigationMenu>
    </div>
  );
};
