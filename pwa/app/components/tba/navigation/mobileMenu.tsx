import { Link } from '@tanstack/react-router';

import MenuIcon from '~icons/lucide/menu';
import XIcon from '~icons/lucide/x';

import {
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuTrigger,
} from '~/components/ui/navigation-menu';
import { NAV_ITEMS_LIST } from '~/lib/navigation/content';
import { cn } from '~/lib/utils';

export function MobileMenuTrigger({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: (open: boolean) => void;
}) {
  return (
    <button
      onClick={() => setOpen(!open)}
      className={cn(
        `z-30 cursor-pointer rounded-full p-2 text-white transition-colors
        duration-200 hover:bg-black/20 md:hidden`,
      )}
    >
      {open ? <XIcon className="size-5" /> : <MenuIcon className="size-5" />}
    </button>
  );
}

export function MobileMenu() {
  return (
    <NavigationMenuItem className="md:hidden">
      <NavigationMenuTrigger
        aria-label="Toggle Menu"
        // Disable hover to open
        onPointerMove={(e) => e.preventDefault()}
      >
        <MenuIcon className="size-5 group-data-[state=open]:hidden" />
        <XIcon className="hidden size-5 group-data-[state=open]:block" />
      </NavigationMenuTrigger>
      <NavigationMenuContent
        className="absolute inset-x-0 top-0 z-12 mt-0 flex max-h-[80svh]
          flex-col overflow-auto px-4 sm:flex-row sm:items-center sm:justify-end
          md:w-fit"
      >
        <ul className="grid divide-y divide-white/10">
          {NAV_ITEMS_LIST.map(({ title, to, icon: Icon }, index) => (
            <Link
              key={title}
              to={to}
              className="flex w-full animate-navigation-item-fade-in
                items-center gap-3 py-4 opacity-0 hover:no-underline"
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <Icon className="size-5 text-white/50" />
              <p className="font-medium text-white">{title}</p>
            </Link>
          ))}
        </ul>
      </NavigationMenuContent>
    </NavigationMenuItem>
  );
}
