import { Link } from '@tanstack/react-router';
import { useState } from 'react';

import GlobalLoadingProgress from '~/components/tba/globalLoadingProgress';
import {
  NavMobile,
  NavMobileButton,
} from '~/components/tba/navigation/navMobile';
import { SearchModal } from '~/components/tba/navigation/searchModal';
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  navigationMenuTriggerStyle,
} from '~/components/ui/navigation-menu';
import lamp from '~/images/tba/tba-lamp.svg';
import { NAV_ITEMS_LIST } from '~/lib/navigation/content';
import { FileRouteTypes } from '~/routeTree.gen';

interface MenuItemProps {
  className?: string;
  to?: FileRouteTypes['to'];
  params?: Record<string, string>;
  href?: string;
  icon: React.ReactNode;
  title: string;
}

export const MenuItem = ({
  className,
  icon,
  title,
  to,
  href,
  params,
}: MenuItemProps) => {
  return (
    <NavigationMenuItem className={className}>
      <NavigationMenuLink
        className={navigationMenuTriggerStyle() + ' cursor-pointer'}
        asChild
      >
        {to ? (
          <Link to={to} params={params} className="hover:no-underline">
            {icon}
            <span>{title}</span>
          </Link>
        ) : href ? (
          <a href={href} className="hover:no-underline">
            {icon}
            <span>{title}</span>
          </a>
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

export const Nav = () => {
  const [mobileNavOpen, setMobileNavOpen] = useState<boolean>(false);
  return (
    <>
      <GlobalLoadingProgress />
      <div
        className="fixed z-15 w-full grow justify-center bg-primary shadow-md"
      >
        <NavigationMenu className="flex justify-between gap-6 px-4 py-2.5">
          <Link
            to="/"
            className="flex items-center gap-3 hover:no-underline max-md:flex-1"
          >
            <img
              src={lamp}
              className="size-6 max-w-none"
              alt="The Blue Alliance Logo"
            />
            <div
              className="text-xl font-medium tracking-tight whitespace-nowrap
                text-white"
            >
              <span className="md:hidden lg:block">The Blue Alliance</span>
              <span className="hidden md:block lg:hidden">TBA</span>
            </div>
          </Link>
          <NavigationMenuList className="flex w-full flex-1">
            {/* Desktop Menu Items */}
            {NAV_ITEMS_LIST.map((item) => (
              <MenuItem
                key={item.title}
                className="hidden md:block"
                icon={<item.icon />}
                title={item.title}
                to={item.to}
                href={item.href}
              />
            ))}
          </NavigationMenuList>
          <div className="space-x-2">
            <SearchModal />
            <NavMobileButton open={mobileNavOpen} setOpen={setMobileNavOpen} />
          </div>
        </NavigationMenu>
        <NavMobile open={mobileNavOpen} setOpen={setMobileNavOpen} />
      </div>
    </>
  );
};
