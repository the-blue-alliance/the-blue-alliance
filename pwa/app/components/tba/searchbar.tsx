import FlexSearch from 'flexsearch';
import { uniq } from 'lodash-es';
import { useEffect, useState } from 'react';

import { Team } from '~/api/v3';
import {
  Command,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '~/components/ui/command';
import { dbGetTeams, dbHasTeams, dbPopulateTeams } from '~/lib/indexedDb';

export default function Searchbar() {
  const [query, setQuery] = useState('');
  const [index, _] = useState<FlexSearch.Document<Team>>(
    new FlexSearch.Document<Team>({
      tokenize: 'forward',
      document: {
        id: 'key',
        field: ['nickname'],
      },
    }),
  );
  const [searchResults, setSearchResults] = useState<FlexSearch.Id[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [teamIdToInfo, setTeamIdToInfo] = useState<Record<string, Team>>({});

  useEffect(() => {
    const setupTeams = async () => {
      if (!(await dbHasTeams())) {
        await dbPopulateTeams();
      }

      void dbGetTeams().then((teams) => {
        if (teams === undefined) {
          return;
        }

        teams.forEach((team) => {
          index.add(team.key, team);
        });

        setTeamIdToInfo(
          teams.reduce<Record<string, Team>>((acc, team) => {
            acc[team.key] = team;
            return acc;
          }, {}),
        );
      });
    };

    void setupTeams();
  }, []);

  useEffect(() => {
    const results = index.search(query, { enrich: true, limit: 20 });
    setSearchResults(uniq(results.flatMap((x) => x.result)));
  }, [query]);

  return (
    <Command className="relative" shouldFilter={false}>
      <CommandInput
        placeholder="Search"
        onFocus={() => {
          setIsOpen(true);
        }}
        onBlur={() => {
          setIsOpen(false);
        }}
        onValueChange={(e) => {
          setQuery(e);
        }}
      />
      {isOpen && (
        <CommandList className="fixed top-14 z-50  w-64 border border-gray-200 bg-white shadow-lg">
          <CommandGroup heading="Teams">
            {searchResults.map((team) => (
              <CommandItem
                key={team}
              >{`${teamIdToInfo[team].team_number} - ${teamIdToInfo[team].nickname}`}</CommandItem>
            ))}
          </CommandGroup>
          {/* <CommandSeparator />
          <CommandGroup heading="Settings">
            <CommandItem>Profile</CommandItem>
            <CommandItem>Billing</CommandItem>
            <CommandItem>Settings</CommandItem>
          </CommandGroup> */}
        </CommandList>
      )}
    </Command>
  );
}
