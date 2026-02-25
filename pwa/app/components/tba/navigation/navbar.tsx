import { Link, useRouter } from '@tanstack/react-router';
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
  const [selected, setSelected] = useState<string>('');
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = router.subscribe('onBeforeNavigate', () => {
      setSelected('');
    });
    return () => unsubscribe();
  }, [router, setSelected]);

  return (
    <>
      <GlobalLoadingProgress />
      <NavigationMenu value={selected} onValueChange={setSelected} asChild>
        <header className="sticky top-0 z-10 h-14 w-full bg-primary shadow-md">
          <div className="container">
            <NavigationMenuList
              asChild
              className="flex h-14 w-full items-center justify-between"
            >
              <nav>
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
                    className="text-xl font-medium tracking-tight
                      whitespace-nowrap text-white"
                  >
                    <span className="sm:hidden md:block">
                      The Blue Alliance
                    </span>
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
                        className={`flex cursor-pointer items-center
                        justify-start gap-2 bg-primary px-2.5 py-2 font-medium
                        text-white hover:bg-black/20 hover:text-white`}
                        asChild
                      >
                        <Link
                          to={to}
                          params={params}
                          className="hover:no-underline"
                        >
                          <Icon className="text-inherit" />
                          <span>{title}</span>
                        </Link>
                      </NavigationMenuLink>
                    </NavigationMenuItem>
                  ))}
                </ul>
                <ul className="flex items-center gap-2">
                  <a
                    href="https://www.thebluealliance.com"
                    className="rounded-md px-2.5 py-2 text-xs font-medium
                      text-white hover:bg-black/20 hover:no-underline
                      max-sm:hidden"
                  >
                    Leave beta
                  </a>
                  <SearchModal />
                  <MobileMenu />
                </ul>
              </nav>
            </NavigationMenuList>
          </div>
          <NavigationMenuViewport />
        </header>
      </NavigationMenu>
    </>
  );
}
