import { DialogProps } from '@radix-ui/react-dialog';
import { useQuery } from '@tanstack/react-query';
import { ClientOnly, useNavigate } from '@tanstack/react-router';
import { useEffect, useMemo, useRef, useState } from 'react';

import SearchIcon from '~icons/lucide/search';

import { SearchIndex } from '~/api/tba/read';
import { getSearchIndexOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { Button } from '~/components/ui/button';
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '~/components/ui/command';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
import { Kbd, KbdGroup } from '~/components/ui/kbd';
import { Spinner } from '~/components/ui/spinner';
import FuzzysortFilterer from '~/lib/search/fuzzysortFilterer';
import { cn } from '~/lib/utils';

export function SearchModal({ ...props }: DialogProps) {
  const [open, setOpen] = useState<boolean>(false);
  const [query, setQuery] = useState<string>('');
  const searchIndexQuery = useQuery(getSearchIndexOptions({}));
  const filterer = useMemo(() => new FuzzysortFilterer(), []);
  const navigate = useNavigate();
  const isMacintosh =
    typeof navigator !== 'undefined'
      ? navigator.userAgent.includes('Macintosh')
      : false;

  const searchResults: SearchIndex | null = useMemo(() => {
    if (!searchIndexQuery.data) {
      return null;
    }
    return filterer.filter(searchIndexQuery.data, query);
  }, [query, searchIndexQuery.data, filterer]);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === 'k' && (e.metaKey || e.ctrlKey)) || e.key === '/') {
        if (
          (e.target instanceof HTMLElement && e.target.isContentEditable) ||
          e.target instanceof HTMLInputElement ||
          e.target instanceof HTMLTextAreaElement ||
          e.target instanceof HTMLSelectElement
        ) {
          return;
        }
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => {
      document.removeEventListener('keydown', down);
    };
  }, []);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="secondary"
          className={cn(
            `bg-surface relative h-9 w-full justify-start rounded-lg bg-white
            pl-4 font-normal text-muted-foreground shadow-none hover:bg-white
            max-lg:hidden sm:pr-12 md:w-32 lg:w-56 xl:w-64 dark:bg-card`,
          )}
          onClick={() => setOpen(true)}
          {...props}
        >
          <span className="hidden xl:inline-flex">
            Search teams and events...
          </span>
          <span className="inline-flex xl:hidden">Search...</span>
          <ClientOnly>
            <div className="absolute top-2 right-1.5 hidden gap-1 sm:flex">
              <KbdGroup>
                <Kbd>{isMacintosh ? '⌘' : 'Ctrl'}</Kbd>
                <Kbd>K</Kbd>
              </KbdGroup>
            </div>
          </ClientOnly>
        </Button>
      </DialogTrigger>

      <DialogTrigger
        className="z-30 cursor-pointer rounded-full p-2 text-white
          transition-colors duration-200 hover:bg-black/20 lg:hidden"
      >
        <SearchIcon className="size-5" />
      </DialogTrigger>

      <DialogContent
        showCloseButton={false}
        className="top-[10%] translate-y-0 rounded-2xl border-none
          bg-clip-padding p-2 shadow-2xl"
      >
        <DialogHeader className="sr-only">
          <DialogTitle>Search...</DialogTitle>
        </DialogHeader>
        <Command
          className="rounded-none bg-transparent
            **:data-[slot=command-input]:h-9! **:data-[slot=command-input]:py-0
            **:data-[slot=command-input-wrapper]:mb-0
            **:data-[slot=command-input-wrapper]:h-10!
            **:data-[slot=command-input-wrapper]:rounded-xl
            **:data-[slot=command-input-wrapper]:border
            **:data-[slot=command-input-wrapper]:border-input
            **:data-[slot=command-input-wrapper]:bg-transparent"
          shouldFilter={false}
        >
          <div className="relative">
            <CommandInput
              placeholder="Search teams and events..."
              value={query}
              onValueChange={setQuery}
              className="h-20 text-base"
            />
            {searchIndexQuery.isLoading && (
              <div
                className="pointer-events-none absolute top-1/2 right-3 z-10
                  flex -translate-y-1/2 items-center justify-center"
              >
                <Spinner className="size-4 text-muted-foreground" />
              </div>
            )}
          </div>
          <CommandList className="no-scrollbar scroll-pt-2 scroll-pb-1.5">
            {searchResults?.teams && searchResults.teams.length > 0 && (
              <CommandGroup
                heading="Teams"
                className="p-0! **:[[cmdk-group-heading]]:scroll-mt-16
                  **:[[cmdk-group-heading]]:p-3!
                  **:[[cmdk-group-heading]]:pb-1!"
              >
                {searchResults.teams.map((team) => (
                  <SearchItem
                    key={team.key}
                    value={team.key}
                    onSelect={() => {
                      void navigate({ to: `/team/${team.key.substring(3)}` });
                      setOpen(false);
                    }}
                  >
                    {team.key.substring(3)} - {team.nickname}
                  </SearchItem>
                ))}
              </CommandGroup>
            )}
            {searchResults?.events && searchResults.events.length > 0 && (
              <CommandGroup
                heading="Events"
                className="p-0! **:[[cmdk-group-heading]]:scroll-mt-16
                  **:[[cmdk-group-heading]]:p-3!
                  **:[[cmdk-group-heading]]:pb-1!"
              >
                {searchResults.events.map((event) => (
                  <SearchItem
                    key={event.key}
                    value={event.key}
                    onSelect={() => {
                      void navigate({ to: `/event/${event.key}` });
                      setOpen(false);
                    }}
                  >
                    {event.key.substring(0, 4)} {event.name} [
                    {event.key.substring(4)}]
                  </SearchItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

function SearchItem({
  children,
  className,
  ...props
}: React.ComponentProps<typeof CommandItem> & {
  onHighlight?: () => void;
  'data-selected'?: string;
  'aria-selected'?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  return (
    <CommandItem
      ref={ref}
      className={cn(
        `h-9 truncate rounded-md px-3! font-medium
        data-[selected=true]:bg-input/50`,
        className,
      )}
      {...props}
    >
      {children}
    </CommandItem>
  );
}
