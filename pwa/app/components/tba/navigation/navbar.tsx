import { Link } from '@tanstack/react-router';
import { useState } from 'react';

import GlobalLoadingProgress from '~/components/tba/globalLoadingProgress';
import {
  MobileMenu,
  MobileMenuTrigger,
} from '~/components/tba/navigation/mobileMenu';
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

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
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
          <NavigationMenuList className="flex w-full flex-1 max-md:hidden">
            {/* Desktop Menu Items */}
            {NAV_ITEMS_LIST.map(({ title, to, icon: Icon }) => (
              <NavigationMenuItem key={title}>
                <NavigationMenuLink
                  className={navigationMenuTriggerStyle() + ' cursor-pointer'}
                  asChild
                >
                  <Link to={to} className="hover:no-underline">
                    <Icon />
                    <span>{title}</span>
                  </Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            ))}
          </NavigationMenuList>
          <div className="space-x-2">
            <SearchModal />
            <MobileMenuTrigger
              open={mobileMenuOpen}
              setOpen={setMobileMenuOpen}
            />
          </div>
        </NavigationMenu>
        <MobileMenu open={mobileMenuOpen} setOpen={setMobileMenuOpen} />
      </div>
    </>
  );
}
