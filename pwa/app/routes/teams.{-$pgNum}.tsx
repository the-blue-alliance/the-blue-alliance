import { createFileRoute, notFound } from '@tanstack/react-router';
import { useEffect, useMemo, useState } from 'react';

import { getSearchIndex, getTeamsSimple } from '~/api/tba/read';
import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';
import TeamListTable from '~/components/tba/teamListTable';
import {
  parseParamsForTeamPgNumElseDefault,
  removeNonNumeric,
} from '~/lib/utils';

const TEAMS_PER_PAGE = 1000;

function getPageNumberFromTeamKey(teamKey: string): number {
  // 1-indexed, 1-999 is page 1, 1000-1999 is page 2, etc.
  return 1 + Math.floor(Number(removeNonNumeric(teamKey)) / TEAMS_PER_PAGE);
}

export const Route = createFileRoute('/teams/{-$pgNum}')({
  loader: async ({ params }) => {
    const searchIndex = await getSearchIndex({});
    if (searchIndex.data === undefined) {
      throw new Error('Failed to load search index');
    }
    const searchTeams = searchIndex.data.teams;

    const maxPageNum = getPageNumberFromTeamKey(
      searchTeams[searchTeams.length - 1].key,
    );
    const selectedPageNum = parseParamsForTeamPgNumElseDefault(
      params,
      maxPageNum,
    );
    if (selectedPageNum === undefined) {
      throw notFound();
    }

    const [teamsSetOne, teamsSetTwo] = await Promise.all([
      getTeamsSimple({ path: { page_num: 2 * (selectedPageNum - 1) } }),
      getTeamsSimple({ path: { page_num: 2 * (selectedPageNum - 1) + 1 } }),
    ]);
    if (teamsSetOne.data === undefined || teamsSetTwo.data === undefined) {
      throw new Error('Failed to load teams');
    }
    const teams = teamsSetOne.data.concat(teamsSetTwo.data);

    const teamCountPerPage = new Map<number, number>();
    for (const team of searchTeams) {
      const page = getPageNumberFromTeamKey(team.key);
      teamCountPerPage.set(page, (teamCountPerPage.get(page) ?? 0) + 1);
    }

    return { teams, teamCountPerPage, selectedPageNum, maxPageNum };
  },
  head: () => {
    return {
      meta: [
        { title: 'FIRST Robotics Teams - The Blue Alliance' },
        {
          name: 'description',
          content: `List of teams in the FIRST Robotics Competition.`,
        },
      ],
    };
  },
  component: TeamsPage,
});

function TeamPageNumberToRange(pageNum: number): string {
  // Page number is 1-indexed
  if (pageNum === 1) {
    return '1-999';
  }
  const thousand = (pageNum - 1) % 1000;
  return `${thousand}000s`;
}

function TeamsPage() {
  const { teams, teamCountPerPage, selectedPageNum, maxPageNum } =
    Route.useLoaderData();
  const [inView, setInView] = useState<Set<string>>(new Set());

  const totalTeamCount = useMemo(() => {
    return Array.from(teamCountPerPage.values()).reduce(
      (acc, count) => acc + count,
      0,
    );
  }, [teamCountPerPage]);

  const tocItems = useMemo(() => {
    return Array.from({ length: maxPageNum }, (_, i) => {
      return { slug: `page-${i + 1}`, label: TeamPageNumberToRange(i + 1) };
    });
  }, [maxPageNum]);

  useEffect(() => {
    const sectionId = `page-${selectedPageNum}`;
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ block: 'start' });
    }
  }, [selectedPageNum]);

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView} />
      <div className="basis-full py-8 lg:basis-5/6">
        <h1 className="mb-3 text-3xl font-medium">
          <i>FIRST</i> Robotics Competition Teams{' '}
          <small className="text-xl text-slate-500">
            {totalTeamCount}&nbsp;Teams
          </small>
        </h1>
        {Array.from({ length: maxPageNum }, (_, i) => {
          const teamCount = teamCountPerPage.get(i + 1) ?? 0;
          return (
            <TableOfContentsSection
              key={i}
              id={`page-${i + 1}`}
              setInView={setInView}
            >
              <h2 key={i} className="mt-5 scroll-mt-12 text-3xl lg:scroll-mt-4">
                Teams {TeamPageNumberToRange(i + 1)}{' '}
                <small className="text-xl text-slate-500">
                  {teamCount} Teams
                </small>
              </h2>
              {selectedPageNum === i + 1 ? (
                <TeamListTable teams={teams} />
              ) : (
                <div className="h-[2000px]" />
              )}
            </TableOfContentsSection>
          );
        })}
      </div>
    </div>
  );
}
