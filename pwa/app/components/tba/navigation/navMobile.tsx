import { Link, useRouter } from '@tanstack/react-router';
import { useEffect } from 'react';

import MenuIcon from '~icons/lucide/menu';
import XIcon from '~icons/lucide/x';

import Searchbar from '~/components/tba/navigation/searchbar';
import { NAV_ITEMS_LIST } from '~/lib/navigation/content';
import { cn } from '~/lib/utils';

export function NavMobileButton({
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

export function NavMobile({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: (open: boolean) => void;
}) {
  const router = useRouter();

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
  }, [open]);

  useEffect(() => {
    const unsubscribe = router.subscribe('onBeforeNavigate', () => {
      setOpen(false);
    });
    return () => unsubscribe();
  }, [router, setOpen]);

  return (
    <nav
      className={cn(
        `fixed inset-0 z-10 hidden max-h-screen w-full overflow-y-auto
        bg-zinc-50 px-5 py-20 lg:hidden dark:bg-black dark:text-white/70`,
        open && 'block',
      )}
    >
      <div className="mb-4">
        <Searchbar className="border" />
      </div>
      <ul className="grid divide-y divide-neutral-200 dark:divide-white/15">
        {NAV_ITEMS_LIST.map(({ title, href, icon: Icon }) => (
          <Link
            key={title}
            to={href}
            className="flex w-full items-center gap-3 py-4"
          >
            <Icon className="size-5 text-neutral-500" />
            <p className="font-medium text-foreground">{title}</p>
          </Link>
        ))}
      </ul>
    </nav>
  );
}
