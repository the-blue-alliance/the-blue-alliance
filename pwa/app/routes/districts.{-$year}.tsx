import { useSuspenseQueries, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';
import { useMemo } from 'react';

import {
  getDistrictTeamsKeysOptions,
  getDistrictsByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { DistrictLink } from '~/components/tba/links';
import { YearSelector } from '~/components/tba/yearSelector';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { staleTimeForYear } from '~/lib/queryClient';
import {
  parseParamsForYearElseDefault,
  publicCacheControlHeaders,
  useValidYears,
} from '~/lib/utils';

export const Route = createFileRoute('/districts/{-$year}')({
  loader: async ({ params, context: { queryClient, currentSeason } }) => {
    const year = parseParamsForYearElseDefault(currentSeason, params);
    if (year === undefined) {
      throw notFound();
    }

    const yearStaleTime = staleTimeForYear(year);

    const districts = await queryClient.ensureQueryData({
      ...getDistrictsByYearOptions({ path: { year } }),
      staleTime: yearStaleTime,
    });

    await Promise.all(
      districts.map((district) =>
        queryClient.ensureQueryData({
          ...getDistrictTeamsKeysOptions({
            path: { district_key: district.key },
          }),
          staleTime: yearStaleTime,
        }),
      ),
    );

    return { year };
  },
  headers: publicCacheControlHeaders(),
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [
          { title: 'FIRST Robotics Districts - The Blue Alliance' },
          {
            name: 'description',
            content: 'District list for the FIRST Robotics Competition.',
          },
        ],
      };
    }

    return {
      meta: [
        {
          title: `${loaderData.year} FIRST Robotics Districts - The Blue Alliance`,
        },
        {
          name: 'description',
          content: `District list for the ${loaderData.year} FIRST Robotics Competition.`,
        },
      ],
    };
  },
  component: DistrictsPage,
});

function DistrictsPage() {
  const { year } = Route.useLoaderData();
  const yearStaleTime = staleTimeForYear(year);
  const { data: districts } = useSuspenseQuery({
    ...getDistrictsByYearOptions({ path: { year } }),
    staleTime: yearStaleTime,
  });
  const validYears = useValidYears();
  const sortedDistricts = useMemo(
    () =>
      [...districts].sort((a, b) =>
        a.display_name.localeCompare(b.display_name),
      ),
    [districts],
  );

  const teamKeyResults = useSuspenseQueries({
    queries: districts.map((district) => ({
      ...getDistrictTeamsKeysOptions({ path: { district_key: district.key } }),
      staleTime: yearStaleTime,
    })),
  });

  const teamKeyCounts = teamKeyResults.map((result) => result.data.length);

  const teamCountByDistrict = useMemo(() => {
    const map = new Map<string, number>();
    districts.forEach((district, i) => {
      map.set(district.key, teamKeyCounts[i]);
    });
    return map;
  }, [districts, teamKeyCounts]);

  return (
    <div className="py-8">
      <div className="mb-4 flex items-center gap-4">
        <h1 className="text-3xl font-medium">
          {year} <i>FIRST</i> Robotics Competition Districts{' '}
          <small className="text-xl text-muted-foreground">
            {districts.length} Districts
          </small>
        </h1>
        <YearSelector
          currentLabel={String(year)}
          triggerClassName="w-[120px]"
          options={validYears.map((y) => ({
            label: String(y),
            to: `/districts/${y}`,
            isCurrent: y === year,
          }))}
        />
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>District</TableHead>
            <TableHead>Key</TableHead>
            <TableHead className="text-right">Teams</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedDistricts.map((district) => (
            <TableRow key={district.key}>
              <TableCell>
                <DistrictLink
                  districtAbbreviation={district.abbreviation}
                  year={year}
                >
                  {district.display_name}
                </DistrictLink>
              </TableCell>
              <TableCell className="font-mono text-muted-foreground">
                {district.abbreviation}
              </TableCell>
              <TableCell className="text-right numeric-data">
                {teamCountByDistrict.get(district.key)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
