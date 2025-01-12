import { useNavigate } from '@remix-run/react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { SearchIndex } from '~/api/v3';
import { EventLink, TeamLink } from '~/components/tba/links';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '~/components/ui/command';
import FuzzysortFilterer from '~/lib/search/fuzzysortFilterer';
import { ProdAPIProvider } from '~/lib/search/prodAPIProvider';
import { cn } from '~/lib/utils';

export default function Searchbar() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const provider = useMemo(() => new ProdAPIProvider(), []);
  const filterer = useMemo(() => new FuzzysortFilterer(), []);

  const [fullSearchData, setFullSearchData] = useState<SearchIndex | null>(
    null,
  );

  useEffect(() => {
    provider
      .provide()
      .then((data) => {
        setFullSearchData(data);
      })
      .catch(() => {
        // todo: log in sentry
      });
  }, [provider]);

  const [searchResults, setSearchResults] = useState<SearchIndex | null>(null);

  useEffect(() => {
    if (fullSearchData === null) {
      return;
    }

    const searchResults = filterer.filter(fullSearchData, query);
    setSearchResults(searchResults);
  }, [query, fullSearchData, filterer]);

  const inputRef = useRef<HTMLInputElement | null>(null);

  // Toggle the menu when ⌘K or ctrl-k is pressed
  useEffect(() => {
    function listener(e: KeyboardEvent) {
      if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setIsOpen((o) => !o);

        if (isOpen) {
          inputRef.current?.blur();
        } else {
          inputRef.current?.focus();
        }
      }
    }

    document.addEventListener('keydown', listener);

    return () => {
      document.removeEventListener('keydown', listener);
    };
  });

  return (
    <Command className="relative" shouldFilter={false}>
      <CommandInput
        placeholder="Search"
        onFocus={() => {
          setIsOpen(true);
        }}
        onBlur={(e) => {
          setIsOpen(false);

          // When the user clicks a CommandItem, the CommandInput loses focus
          // For some reason, this prevents the CommandItem onClick from working.
          // It also doesn't follow a clicked href for some reason.
          // Here, if we lose focus because we clicked on something else, manually
          // fire a click event.
          // There has to be a better solution than this, but this is the best I've got.
          if (e.relatedTarget !== null) {
            e.relatedTarget.dispatchEvent(new MouseEvent('click'));
          }
        }}
        onValueChange={(e) => {
          setQuery(e);
        }}
        ref={inputRef}
        className="h-8"
      />

      <CommandList
        className={cn(
          'fixed top-14 z-50  w-64 border border-gray-200 bg-white shadow-lg',
          {
            hidden: !isOpen,
          },
        )}
      >
        {searchResults?.teams && searchResults.teams.length > 0 && (
          <CommandGroup heading="Teams">
            {searchResults.teams.map((team) => (
              <CommandItem
                key={team.key}
                onSelect={() => {
                  navigate(`/team/${team.key.substring(3)}`);
                  setIsOpen(false);
                }}
                asChild
              >
                <TeamLink teamOrKey={team.key}>
                  {team.key.substring(3)} - {team.nickname}
                </TeamLink>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {searchResults?.events && searchResults.events.length > 0 && (
          <CommandGroup heading="Events">
            {searchResults.events.map((event) => (
              <CommandItem
                key={event.key}
                onSelect={() => {
                  navigate(`/event/${event.key}`);
                  setIsOpen(false);
                }}
              >
                <EventLink eventOrKey={event.key}>
                  {event.key.substring(0, 4)} {event.name} [
                  {event.key.substring(4)}]
                </EventLink>
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {searchResults === null ||
          (searchResults.teams.length === 0 &&
            searchResults.events.length === 0 && (
              <CommandEmpty>No Results Found</CommandEmpty>
            ))}
      </CommandList>
    </Command>
  );
}
