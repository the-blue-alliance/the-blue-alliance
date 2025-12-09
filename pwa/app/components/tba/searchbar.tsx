import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useRef, useState } from 'react';

import { SearchIndex } from '~/api/tba/read';
import { getSearchIndexOptions } from '~/api/tba/read/@tanstack/react-query.gen';
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
import { cn } from '~/lib/utils';

export default function Searchbar() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const fullSearchData = useQuery(getSearchIndexOptions({})).data;
  const filterer = useMemo(() => new FuzzysortFilterer(), []);
  const searchResults: SearchIndex | null = useMemo(() => {
    if (!fullSearchData) {
      return null;
    }
    return filterer.filter(fullSearchData, query);
  }, [query, fullSearchData, filterer]);

  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    function listener(e: KeyboardEvent) {
      // Toggle the menu when ⌘K or ctrl-k is pressed
      if (e.key === 'k' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        setIsOpen((o) => !o);

        if (isOpen) {
          inputRef.current?.blur();
        } else {
          inputRef.current?.focus();
        }
      }

      // Dismiss menu when escape is pressed
      if (e.key === 'Escape') {
        setIsOpen(false);
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
          `fixed top-14 z-50 w-64 rounded-lg border border-gray-200 bg-white
          shadow-lg`,
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
                  setIsOpen(false);
                }}
                asChild
              >
                <TeamLink
                  teamOrKey={team.key}
                  className="cursor-pointer hover:no-underline"
                >
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
                  setIsOpen(false);
                }}
                asChild
              >
                <EventLink
                  eventOrKey={event.key}
                  className="cursor-pointer hover:no-underline"
                >
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
