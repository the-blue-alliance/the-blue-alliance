import type { ColumnVisibilityState } from '@tanstack/react-table';

import type { EventCoprs } from '~/api/tba/read';

export function getDefaultTeleopComponentName(year: number): string {
  if (year == 2015) {
    return 'teleop_points';
  }

  if (year < 2026) {
    return 'teleopPoints';
  }

  return 'totalTeleopPoints';
}

export function getDefaultAutoComponentName(year: number): string {
  if (year == 2015) {
    return 'auto_points';
  }

  if (year < 2026) {
    return 'autoPoints';
  }

  return 'totalAutoPoints';
}

export function getDefaultTotalComponentName(year: number): string {
  if (year == 2015) {
    return 'total_points';
  }

  return 'totalPoints';
}

export interface CoprRow {
  teamKey: string;
  values: Record<string, number>;
}

export interface CoprTableModel {
  componentNames: string[];
  defaultVisible: ColumnVisibilityState;
  defaultSortComponent: string | null;
  rows: CoprRow[];
}

export function buildCoprTableModel(
  coprs: EventCoprs,
  year: number,
): CoprTableModel {
  const kept = Object.keys(coprs).filter((name) =>
    Object.values(coprs[name]).some((value) => value !== 0),
  );

  const preferred = [
    getDefaultTotalComponentName(year),
    getDefaultAutoComponentName(year),
    getDefaultTeleopComponentName(year),
  ].filter((name) => kept.includes(name));

  const componentNames = [
    ...preferred,
    ...kept.filter((name) => !preferred.includes(name)),
  ];

  const visibleNames =
    preferred.length > 0 ? preferred : componentNames.slice(0, 3);

  const defaultVisible = Object.fromEntries(
    componentNames.map((name) => [name, visibleNames.includes(name)]),
  );

  const totalName = getDefaultTotalComponentName(year);
  const defaultSortComponent = kept.includes(totalName)
    ? totalName
    : (visibleNames[0] ?? null);

  const teamKeys = new Set(
    componentNames.flatMap((name) => Object.keys(coprs[name])),
  );

  const rows = [...teamKeys].map((teamKey) => ({
    teamKey,
    values: Object.fromEntries(
      componentNames
        .filter((name) => teamKey in coprs[name])
        .map((name) => [name, coprs[name][teamKey]]),
    ),
  }));

  return { componentNames, defaultVisible, defaultSortComponent, rows };
}
