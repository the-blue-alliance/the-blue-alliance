import { useQueries, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound } from '@tanstack/react-router';
import { useMemo } from 'react';

import type { DistrictAdvancementCutoffs } from '~/api/tba/read';
import {
  getDistrictAdvancementOptions,
  getDistrictTeamsKeysOptions,
  getDistrictsByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { DistrictLink } from '~/components/tba/links';
import { YearSelector } from '~/components/tba/yearSelector';
import { Skeleton } from '~/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '~/components/ui/tooltip';
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

    await queryClient.ensureQueryData({
      ...getDistrictsByYearOptions({ path: { year } }),
      staleTime: yearStaleTime,
    });

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

function AdvancementCountCell({
  slots,
  teamCount,
}: {
  slots: number;
  teamCount: number | undefined;
}) {
  if (teamCount === undefined) {
    return <TableCell className="text-right numeric-data">{slots}</TableCell>;
  }

  const percentage = Math.round((slots / teamCount) * 100);

  return (
    <TableCell className="text-right numeric-data">
      <Tooltip>
        <TooltipTrigger>{slots}</TooltipTrigger>
        <TooltipContent>{percentage}% of teams</TooltipContent>
      </Tooltip>
    </TableCell>
  );
}

function CutoffCell({
  original,
  effective,
  declines,
  isLoading,
}: {
  original: number | undefined;
  effective: number | undefined;
  declines: number | undefined;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <TableCell className="text-right">
        <Skeleton className="ml-auto h-4 w-8" />
      </TableCell>
    );
  }

  if (effective === undefined || effective <= 0) {
    return <TableCell className="text-right numeric-data">-</TableCell>;
  }

  if (!original || original === effective || !declines) {
    return (
      <TableCell className="text-right numeric-data">{effective}</TableCell>
    );
  }

  return (
    <TableCell className="text-right numeric-data">
      <Tooltip>
        <TooltipTrigger>{effective}</TooltipTrigger>
        <TooltipContent>
          {original} before {declines} declines
        </TooltipContent>
      </Tooltip>
    </TableCell>
  );
}

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

  const teamKeyResults = useQueries({
    queries: districts.map((district) => ({
      ...getDistrictTeamsKeysOptions({ path: { district_key: district.key } }),
      staleTime: yearStaleTime,
    })),
  });

  const teamKeyCounts = teamKeyResults.map((result) => result.data?.length);
  const teamKeyPending = teamKeyResults.map((result) => result.isPending);

  const teamCountPendingByDistrict = useMemo(() => {
    const map = new Map<string, boolean>();
    districts.forEach((district, i) => {
      map.set(district.key, teamKeyPending[i]);
    });
    return map;
  }, [districts, teamKeyPending]);

  const teamCountByDistrict = useMemo(() => {
    const map = new Map<string, number | undefined>();
    districts.forEach((district, i) => {
      map.set(district.key, teamKeyCounts[i]);
    });
    return map;
  }, [districts, teamKeyCounts]);

  const advancementResults = useQueries({
    queries: districts.map((district) => ({
      ...getDistrictAdvancementOptions({
        path: { district_key: district.key },
      }),
      staleTime: yearStaleTime,
    })),
  });

  const cutoffs = advancementResults.map((result) => result.data?.cutoffs);
  const cutoffsPending = advancementResults.map((result) => result.isPending);

  const cutoffsPendingByDistrict = useMemo(() => {
    const map = new Map<string, boolean>();
    districts.forEach((district, i) => {
      map.set(district.key, cutoffsPending[i]);
    });
    return map;
  }, [districts, cutoffsPending]);

  const cutoffsByDistrict = useMemo(() => {
    const map = new Map<
      string,
      DistrictAdvancementCutoffs | null | undefined
    >();
    districts.forEach((district, i) => {
      map.set(district.key, cutoffs[i]);
    });
    return map;
  }, [districts, cutoffs]);

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
            <TableHead className="text-right">DCMP Slots</TableHead>
            <TableHead className="text-right">DCMP Cutoff</TableHead>
            <TableHead className="text-right">CMP Slots</TableHead>
            <TableHead className="text-right">CMP Cutoff</TableHead>
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
                {teamCountPendingByDistrict.get(district.key) ? (
                  <Skeleton className="ml-auto h-4 w-8" />
                ) : (
                  (teamCountByDistrict.get(district.key) ?? '-')
                )}
              </TableCell>
              <AdvancementCountCell
                slots={district.official_advancement_counts.dcmp}
                teamCount={teamCountByDistrict.get(district.key)}
              />
              <CutoffCell
                original={cutoffsByDistrict.get(district.key)?.dcmp_original}
                effective={cutoffsByDistrict.get(district.key)?.dcmp_effective}
                declines={
                  cutoffsByDistrict.get(district.key)?.dcmp_declines.length
                }
                isLoading={cutoffsPendingByDistrict.get(district.key) ?? false}
              />
              <AdvancementCountCell
                slots={district.official_advancement_counts.cmp}
                teamCount={teamCountByDistrict.get(district.key)}
              />
              <CutoffCell
                original={cutoffsByDistrict.get(district.key)?.cmp_original}
                effective={cutoffsByDistrict.get(district.key)?.cmp_effective}
                declines={
                  cutoffsByDistrict.get(district.key)?.cmp_declines.length
                }
                isLoading={cutoffsPendingByDistrict.get(district.key) ?? false}
              />
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
