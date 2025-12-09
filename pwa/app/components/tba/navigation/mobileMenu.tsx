import { Link, useRouter } from '@tanstack/react-router';
import { useEffect } from 'react';

import MenuIcon from '~icons/lucide/menu';
import XIcon from '~icons/lucide/x';

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

export function MobileMenu({
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
        'bg-primary px-5 pb-2 text-white md:hidden',
        open ? 'block' : 'hidden',
      )}
    >
      <ul className="grid divide-y divide-white/10">
        {NAV_ITEMS_LIST.map(({ title, href, icon: Icon }, index) => (
          <Link
            key={title}
            to={href}
            className="flex w-full animate-navigation-item-fade-in items-center
              gap-3 py-4 opacity-0 hover:no-underline"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <Icon className="size-5 text-white/50" />
            <p className="font-medium text-white">{title}</p>
          </Link>
        ))}
      </ul>
    </nav>
  );
}
