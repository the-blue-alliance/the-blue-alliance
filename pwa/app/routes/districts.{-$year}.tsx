import { useSuspenseQueries, useSuspenseQuery } from '@tanstack/react-query';
import { createFileRoute, notFound, useNavigate } from '@tanstack/react-router';
import { useMemo } from 'react';

import {
  getDistrictTeamsKeysOptions,
  getDistrictsByYearOptions,
} from '~/api/tba/read/@tanstack/react-query.gen';
import { DistrictLink } from '~/components/tba/links';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import {
  parseParamsForYearElseDefault,
  publicCacheControlHeaders,
  useValidYears,
} from '~/lib/utils';

export const Route = createFileRoute('/districts/{-$year}')({
  loader: async ({ params, context: { queryClient } }) => {
    const year = await parseParamsForYearElseDefault(queryClient, params);
    if (year === undefined) {
      throw notFound();
    }

    const districts = await queryClient.ensureQueryData(
      getDistrictsByYearOptions({ path: { year } }),
    );

    await Promise.all(
      districts.map((district) =>
        queryClient.ensureQueryData(
          getDistrictTeamsKeysOptions({
            path: { district_key: district.key },
          }),
        ),
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
  const { data: districts } = useSuspenseQuery({
    ...getDistrictsByYearOptions({ path: { year } }),
  });
  const validYears = useValidYears();
  const navigate = useNavigate();

  const sortedDistricts = useMemo(
    () =>
      [...districts].sort((a, b) =>
        a.display_name.localeCompare(b.display_name),
      ),
    [districts],
  );

  const teamKeyResults = useSuspenseQueries({
    queries: districts.map((district) =>
      getDistrictTeamsKeysOptions({ path: { district_key: district.key } }),
    ),
  });

  const teamCountByDistrict = useMemo(() => {
    const map = new Map<string, number>();
    districts.forEach((district, i) => {
      map.set(district.key, teamKeyResults[i].data.length);
    });
    return map;
  }, [districts, teamKeyResults]);

  return (
    <div className="py-8">
      <div className="mb-4 flex items-center gap-4">
        <h1 className="text-3xl font-medium">
          {year} <i>FIRST</i> Robotics Competition Districts{' '}
          <small className="text-xl text-muted-foreground">
            {districts.length} Districts
          </small>
        </h1>
        <Select
          value={String(year)}
          onValueChange={(value) => {
            void navigate({ to: `/districts/${value}` });
          }}
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder={year} />
          </SelectTrigger>
          <SelectContent className="max-h-[30vh] overflow-y-auto">
            {validYears.map((y) => (
              <SelectItem key={y} value={`${y}`}>
                {y}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
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
              <TableCell className="text-right tabular-nums">
                {teamCountByDistrict.get(district.key)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
