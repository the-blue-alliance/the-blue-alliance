import { Link, useLocation, useRouter } from '@tanstack/react-router';
import { useEffect, useState } from 'react';

import GlobalLoadingProgress from '~/components/tba/globalLoadingProgress';
import { MobileMenu } from '~/components/tba/navigation/mobileMenu';
import { SearchModal } from '~/components/tba/navigation/searchModal';
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuViewport,
} from '~/components/ui/navigation-menu';
import lamp from '~/images/tba/tba-lamp.svg';
import { NAV_ITEMS_LIST } from '~/lib/navigation/content';

export function Navbar() {
  // Base UI derives the menu's open state from `value != null`, so the
  // closed state must be null — an empty string counts as "open" and keeps
  // the popup permanently mounted (Radix used '' as its closed sentinel).
  const [selected, setSelected] = useState<string | null>(null);
  const router = useRouter();
  const { pathname } = useLocation();

  useEffect(() => {
    const unsubscribe = router.subscribe('onBeforeNavigate', () => {
      setSelected(null);
    });
    return () => unsubscribe();
  }, [router, setSelected]);

  return (
    <>
      <GlobalLoadingProgress />
      <NavigationMenu
        value={selected}
        onValueChange={(value, eventDetails) => {
          // Base UI opens NavigationMenu triggers on hover (~50ms delay)
          // with no opt-out prop. The only trigger here is the mobile
          // hamburger, which should be click-only, so ignore hover-driven
          // changes (the menu is controlled, so dropping them is enough).
          if (eventDetails.reason === 'trigger-hover') {
            return;
          }
          setSelected((value as string | null) ?? null);
        }}
        render={
          <header className="sticky top-0 z-50 h-14 w-full bg-brand shadow-md" />
        }
      >
        <div className="container">
          <NavigationMenuList
            render={<nav />}
            className="flex h-14 w-full items-center justify-between"
          >
            <Link
              to="/"
              className="flex items-center gap-3 hover:no-underline
                max-md:flex-1"
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
                <span className="sm:hidden md:block">The Blue Alliance</span>
                <span className="hidden sm:block md:hidden">TBA</span>
              </div>
            </Link>
            {/* Desktop Menu Items */}
            <ul
              className="flex list-none flex-row items-center gap-1 px-6
                max-sm:hidden"
            >
              {NAV_ITEMS_LIST.map(({ title, to, params, icon: Icon }) => (
                <NavigationMenuItem key={title}>
                  <NavigationMenuLink
                    className={`flex cursor-pointer items-center justify-start
                    gap-2 bg-brand px-2.5 py-2 font-medium text-white
                    hover:bg-black/20 hover:text-white`}
                    render={
                      <Link
                        to={to}
                        params={params}
                        className="hover:no-underline"
                        activeProps={{ className: 'bg-white/15' }}
                      />
                    }
                  >
                    <Icon className="text-inherit" />
                    <span>{title}</span>
                  </NavigationMenuLink>
                </NavigationMenuItem>
              ))}
            </ul>
            <ul className="flex items-center gap-2">
              <a
                href={`https://www.thebluealliance.com${pathname}`}
                className="rounded-md px-2.5 py-2 text-xs font-medium text-white
                  hover:bg-black/20 hover:no-underline max-sm:hidden"
              >
                Leave beta
              </a>
              <SearchModal />
              <MobileMenu />
            </ul>
          </NavigationMenuList>
        </div>
        <NavigationMenuViewport />
      </NavigationMenu>
    </>
  );
}
