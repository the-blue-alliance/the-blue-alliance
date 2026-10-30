import type { QueryClient } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import type { AnchorHTMLAttributes, ReactNode } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
  AllianceColor,
  CompLevel,
  EventType,
  type Match,
  type Team,
} from '~/api/tba/read';
import { runHead, runLoader } from '~/routes/-testUtils';
import { Route, StatsSection } from '~/routes/team.$teamNumber.{-$year}';

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@tanstack/react-router')>();
  return {
    ...actual,
    Link: ({
      children,
      to,
      ...props
    }: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
      children?: ReactNode;
      to: string;
    }) => (
      <a href={to} {...props}>
        {children}
      </a>
    ),
  };
});

vi.mock('~/components/tba/links', () => ({
  DistrictLink: ({ children }: { children: ReactNode }) => (
    <a href="#district">{children}</a>
  ),
}));

const team = {
  key: 'frc254',
  team_number: 254,
  nickname: 'The Cheesy Poofs',
  city: 'San Jose',
  state_prov: 'CA',
  postal_code: '95112',
  country: 'USA',
};

function load(year: string | undefined, responses: Record<string, unknown>) {
  const queryClient = {
    ensureQueryData: vi.fn<
      (options: { queryKey: [{ _id: string }] }) => Promise<unknown>
    >(({ queryKey }) =>
      queryKey[0]._id in responses
        ? Promise.resolve(responses[queryKey[0]._id])
        : Promise.reject(new Error('500')),
    ),
  } as unknown as QueryClient;
  return runLoader(Route, {
    params: { teamNumber: '254', year },
    context: { queryClient, currentSeason: 2026 },
  });
}

describe('team route loader', () => {
  test('loads a year the team competed in', async () => {
    await expect(
      load('2024', { getTeam: team, getTeamYearsParticipated: [2024] }),
    ).resolves.toEqual({
      teamKey: 'frc254',
      year: 2024,
      avatarYear: 2024,
      team,
    });
  });

  test('uses the most recent active year for the avatar before 2018', async () => {
    await expect(
      load('2015', { getTeam: team, getTeamYearsParticipated: [2015, 2025] }),
    ).resolves.toMatchObject({ avatarYear: 2025 });
  });

  test('throws not-found for an invalid year', async () => {
    await expect(load('abc', {})).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found when the team fails to load', async () => {
    await expect(
      load('2024', { getTeamYearsParticipated: [2024] }),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('throws not-found for a requested year the team skipped', async () => {
    await expect(
      load('2020', { getTeam: team, getTeamYearsParticipated: [2024] }),
    ).rejects.toMatchObject({ isNotFound: true });
  });

  test('redirects to history when the team skipped the current season', async () => {
    await expect(
      load(undefined, { getTeam: team, getTeamYearsParticipated: [2024] }),
    ).rejects.toMatchObject({
      options: {
        to: '/team/$teamNumber/history',
        params: { teamNumber: '254' },
      },
    });
  });

  test('loads the page when the years-participated fetch fails', async () => {
    await expect(load('2020', { getTeam: team })).resolves.toMatchObject({
      year: 2020,
    });
  });

  test('tolerates failed socials and team statuses', async () => {
    await expect(
      load('2024', {
        getTeam: team,
        getTeamYearsParticipated: [2024],
        getTeamMediaByYear: [],
        getTeamMatchesByYear: [],
        getTeamAwardsByYear: [],
        getTeamEventsByYear: [],
        getTeamDistricts: [],
      }),
    ).resolves.toMatchObject({ year: 2024 });
  });

  test('loads the page when remapped robot data fails to load', async () => {
    await expect(
      load('2026', {
        getTeam: team,
        getTeamYearsParticipated: [2026],
        getTeamEventsByYear: [
          { key: '2026nhmm', remap_teams: { frc9997: 'frc254B' } },
        ],
      }),
    ).resolves.toMatchObject({ year: 2026 });
  });
});

describe('StatsSection', () => {
  function alliance(score: number, teamKeys: string[]) {
    return {
      score,
      team_keys: teamKeys,
      surrogate_team_keys: [],
      dq_team_keys: [],
    };
  }

  function makeMatch(overrides: Partial<Match> & { key: string }): Match {
    return {
      comp_level: CompLevel.QM,
      set_number: 1,
      match_number: 1,
      alliances: {
        red: alliance(50, ['frc2791']),
        blue: alliance(40, ['frc1']),
      },
      winning_alliance: AllianceColor.NO_ALLIANCE,
      event_key: overrides.key.split('_')[0],
      time: null,
      actual_time: null,
      predicted_time: null,
      post_result_time: null,
      score_breakdown: null,
      videos: [],
      ...overrides,
    };
  }

  const team2791 = {
    key: 'frc2791',
    team_number: 2791,
  } as Team;

  const events = [
    {
      key: '2015nytr',
      event_type: EventType.REGIONAL,
      year: 2015,
    },
  ] as Parameters<typeof StatsSection>[0]['events'];

  test('shows 2015 average qual and playoff scores instead of a W-L-T', () => {
    render(
      <StatsSection
        events={events}
        team={team2791}
        year={2015}
        remappedRobots={[]}
        matches={[
          makeMatch({
            key: '2015nytr_qm1',
            alliances: {
              red: alliance(44, ['frc2791']),
              blue: alliance(68, ['frc1']),
            },
          }),
          makeMatch({
            key: '2015nytr_qm2',
            match_number: 2,
            alliances: {
              red: alliance(114, ['frc2791']),
              blue: alliance(70, ['frc1']),
            },
          }),
          makeMatch({
            key: '2015nytr_qf1m1',
            comp_level: CompLevel.QF,
            alliances: {
              red: alliance(49, ['frc2791']),
              blue: alliance(137, ['frc1']),
            },
          }),
          makeMatch({
            key: '2015nytr_qf1m2',
            comp_level: CompLevel.QF,
            match_number: 2,
            alliances: {
              red: alliance(82, ['frc2791']),
              blue: alliance(137, ['frc1']),
            },
          }),
        ]}
      />,
    );

    expect(screen.getByText('79.00')).toBeTruthy();
    expect(screen.getByText('65.50')).toBeTruthy();
    expect(screen.getByText(/Overall, Team 2791 had/)).toBeTruthy();
    expect(screen.queryByText(/0-0-/)).toBeNull();
  });

  test('keeps W-L-T summaries for non-2015 seasons', () => {
    render(
      <StatsSection
        events={
          [
            {
              key: '2024nytr',
              event_type: EventType.REGIONAL,
              year: 2024,
            },
          ] as Parameters<typeof StatsSection>[0]['events']
        }
        team={team2791}
        year={2024}
        remappedRobots={[]}
        matches={[
          makeMatch({
            key: '2024nytr_qm1',
            alliances: {
              red: alliance(100, ['frc2791']),
              blue: alliance(80, ['frc1']),
            },
            winning_alliance: AllianceColor.RED,
          }),
        ]}
      />,
    );

    expect(screen.getByText('1-0')).toBeTruthy();
    expect(screen.queryByText(/average qual score/)).toBeNull();
  });
});

describe('team route head', () => {
  test('titles the page with the team', () => {
    expect(runHead(Route, { loaderData: { team } })?.meta?.[0]).toEqual({
      title: 'The Cheesy Poofs - Team 254 - The Blue Alliance',
    });
  });

  test('describes the team location in structured data', () => {
    const head = runHead(Route, { loaderData: { team } });
    expect(
      JSON.parse(head?.scripts?.[0]?.children as string).location.address,
    ).toEqual({
      '@type': 'PostalAddress',
      addressLocality: 'San Jose',
      addressRegion: 'CA',
      postalCode: '95112',
      addressCountry: 'USA',
    });
  });

  test('describes a team with no postal code without printing null', () => {
    expect(
      runHead(Route, {
        loaderData: { team: { ...team, postal_code: null } },
      })?.meta?.[1],
    ).toEqual({
      name: 'description',
      content:
        'From San Jose, CA, USA. Team information, match results, and match videos from the FIRST Robotics Competition.',
    });
  });

  test('omits the location sentence for a team with no location', () => {
    expect(
      runHead(Route, {
        loaderData: {
          team: {
            ...team,
            city: null,
            state_prov: null,
            postal_code: null,
            country: null,
          },
        },
      })?.meta?.[1],
    ).toEqual({
      name: 'description',
      content:
        'Team information, match results, and match videos from the FIRST Robotics Competition.',
    });
  });

  test('falls back to a generic title without loader data', () => {
    expect(runHead(Route)?.meta?.[0]).toEqual({
      title: 'Team Information - The Blue Alliance',
    });
  });
});
