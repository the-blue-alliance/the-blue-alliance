import { useQuery } from '@tanstack/react-query';
import { ClientOnly, useNavigate } from '@tanstack/react-router';
import { cn } from 'cn';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Temporal } from 'temporal-polyfill';

import SearchIcon from '~icons/lucide/search';

import { getSearchIndexOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { Button } from '~/components/ui/button';
import {
  Command,
  CommandEmpty,
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
import defaultAvatar from '~/images/default-avatar.png';
import { STALE_TIME } from '~/lib/queryClient';
import FuzzysortFilterer, {
  SearchResult,
} from '~/lib/search/fuzzysortFilterer';

export function SearchModal() {
  const [open, setOpen] = useState<boolean>(false);
  const [query, setQuery] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);
  // cmdk's selected item, controlled so Enter navigates to exactly what is
  // highlighted (typing, arrows, vim keys, and pointer hover all report through
  // onValueChange) instead of cmdk's asynchronously-committed selection, which
  // can lag a keystroke behind the synchronously reordered list (#10104).
  const [selection, setSelection] = useState<{ query: string; value: string }>({
    query: '',
    value: '',
  });
  const searchIndexQuery = useQuery({
    ...getSearchIndexOptions({}),
    staleTime: STALE_TIME.SEARCH_INDEX,
  });
  const filterer = useMemo(() => new FuzzysortFilterer(), []);
  const navigate = useNavigate();
  const isMacintosh =
    typeof navigator !== 'undefined'
      ? navigator.userAgent.includes('Macintosh')
      : false;

  const searchResults: SearchResult[] | null = useMemo(() => {
    if (!searchIndexQuery.data) {
      return null;
    }
    return filterer.filter(searchIndexQuery.data, query);
  }, [query, searchIndexQuery.data, filterer]);

  // The top result is the default highlight; the user's own pick takes over
  // until the query changes. Derived during render so it never lags a keystroke.
  const selectedResult =
    (selection.query === query
      ? searchResults?.find((r) => r.key === selection.value)
      : undefined) ?? searchResults?.[0];

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

  const isIndexPending = searchIndexQuery.isPending && !searchIndexQuery.data;
  const hasNoResults = searchResults !== null && searchResults.length === 0;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button
            variant="secondary"
            className={cn(
              `relative h-9 w-full justify-start rounded-lg bg-white pl-4
              font-normal text-muted-foreground shadow-none hover:bg-white
              max-lg:hidden sm:pr-12 md:w-32 lg:w-56 xl:w-64 dark:bg-card`,
            )}
          />
        }
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
      </DialogTrigger>

      <DialogTrigger
        aria-label="Search"
        className="z-30 cursor-pointer rounded-full p-2 text-white
          transition-colors duration-200 hover:bg-black/20 lg:hidden"
      >
        <SearchIcon className="size-5" />
      </DialogTrigger>

      <DialogContent
        initialFocus={inputRef}
        showCloseButton={false}
        className="top-[10%] translate-y-0 rounded-2xl border-none
          bg-clip-padding p-2 shadow-2xl dark:bg-neutral-900"
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
          value={selectedResult?.key ?? ''}
          onValueChange={(value) => {
            setSelection({ query, value });
          }}
        >
          <div className="relative">
            <CommandInput
              ref={inputRef}
              placeholder="Search teams and events..."
              value={query}
              onValueChange={setQuery}
              onKeyDown={(e) => {
                if (
                  e.key !== 'Enter' ||
                  e.nativeEvent.isComposing ||
                  !selectedResult
                ) {
                  return;
                }
                // Stop cmdk's root keydown handler from also navigating to its
                // (possibly stale) aria-selected item.
                e.preventDefault();
                e.stopPropagation();
                void navigate({ to: selectedResult.path });
                setOpen(false);
              }}
              className="h-20 text-base"
            />
            {isIndexPending && (
              <div
                className="pointer-events-none absolute top-1/2 right-3 z-10
                  flex -translate-y-1/2 items-center justify-center"
              >
                <Spinner className="size-4 text-muted-foreground" />
              </div>
            )}
          </div>
          <CommandList className="no-scrollbar scroll-pt-2 scroll-pb-1.5">
            {isIndexPending && (
              <div
                data-testid="search-index-loading"
                className="py-6 text-center text-sm text-muted-foreground"
              >
                Loading teams and events…
              </div>
            )}
            {searchIndexQuery.isError && !searchIndexQuery.data && (
              <div
                data-testid="search-index-error"
                className="py-6 text-center text-sm text-muted-foreground"
              >
                Failed to load search data. Try again later.
              </div>
            )}
            {searchResults && searchResults.length > 0 && (
              <CommandGroup className="p-0! pt-2!">
                {searchResults.map((result) => (
                  <SearchItem
                    key={result.key}
                    value={result.key}
                    onSelect={() => {
                      void navigate({ to: result.path });
                      setOpen(false);
                    }}
                  >
                    {result.type === 'team' && (
                      <SearchTeamAvatar teamKey={result.key} />
                    )}
                    <span className="truncate">{result.label}</span>
                  </SearchItem>
                ))}
              </CommandGroup>
            )}
            {hasNoResults && <CommandEmpty>No results found.</CommandEmpty>}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

function SearchTeamAvatar({ teamKey }: { teamKey: string }) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const year = Temporal.Now.plainDateISO().year;

  return (
    <span className="size-6 shrink-0">
      <img
        alt={failed ? 'Default Team Avatar' : 'Team Avatar'}
        src={
          failed
            ? defaultAvatar
            : `https://www.thebluealliance.com/avatar/${year}/${teamKey}.png`
        }
        onLoad={() => setLoaded(true)}
        onError={() => setFailed(true)}
        className={cn(
          'size-full transition-opacity duration-200',
          loaded ? 'opacity-100' : 'opacity-0',
        )}
      />
    </span>
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
