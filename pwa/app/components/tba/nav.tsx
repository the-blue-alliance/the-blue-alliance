import { Link } from 'react-router';

import BiBarChartLineFill from '~icons/bi/bar-chart-line-fill';
import BiCameraVideoFill from '~icons/bi/camera-video-fill';
import BiGearFill from '~icons/bi/gear-fill';
import BiPencilFill from '~icons/bi/pencil-fill';
import BiPeopleFill from '~icons/bi/people-fill';
import BiStarFill from '~icons/bi/star-fill';
import BiThreeDotsVertical from '~icons/bi/three-dots-vertical';
import IonCalendar from '~icons/ion/calendar';

import Searchbar from '~/components/tba/searchbar';
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
        `text-md relative flex cursor-default items-center rounded-sm bg-primary
        outline-hidden transition-colors select-none focus:bg-background
        focus:text-accent-foreground data-disabled:pointer-events-none
        data-disabled:opacity-50`,
        className,
      )}
    >
      <NavigationMenuLink
        className={
          navigationMenuTriggerStyle() +
          ' w-full grow cursor-pointer hover:no-underline'
        }
        asChild
      >
        {route ? (
          <Link
            to={route}
            className="flex grow flex-row flex-wrap content-between items-center justify-start px-2
              text-white hover:no-underline"
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
      <NavigationMenu className="gap-6 px-4 py-2.5">
        <Link to="/" className="flex items-center gap-3 hover:no-underline">
          <img
            src={lamp}
            className="size-6 max-w-none"
            alt="The Blue Alliance Logo"
          />
          <div className="hidden text-xl font-medium tracking-tight whitespace-nowrap text-white lg:block">
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
            route="/teams"
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
                `shadow-l m-0 mt-6 w-30 rounded-md border-none bg-primary px-1 py-1
                drop-shadow-lg`,
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
              <DropMenuItem
                icon={<BiGearFill />}
                title="Account"
                route="/account"
              />
            </PopoverContent>
          </Popover>
        </NavigationMenuList>
        <Searchbar />
      </NavigationMenu>
    </div>
  );
};
