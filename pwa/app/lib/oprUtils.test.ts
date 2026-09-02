import { describe, expect, test } from 'vitest';

import { buildCoprTableModel } from '~/lib/oprUtils';

describe.concurrent('buildCoprTableModel', () => {
  test('drops components whose values are all zero', () => {
    const model = buildCoprTableModel(
      {
        totalPoints: { frc254: 88.4, frc1678: 84.1 },
        unusedPoints: { frc254: 0, frc1678: 0 },
      },
      2024,
    );

    expect(model.componentNames).toEqual(['totalPoints']);
    expect(model.defaultVisible).toEqual({ totalPoints: true });
    expect(model.rows).toEqual([
      { teamKey: 'frc254', values: { totalPoints: 88.4 } },
      { teamKey: 'frc1678', values: { totalPoints: 84.1 } },
    ]);
  });

  test('keeps a component when a single team is nonzero', () => {
    const model = buildCoprTableModel(
      { totalPoints: { frc254: 0, frc1678: 0.5 } },
      2024,
    );

    expect(model.componentNames).toEqual(['totalPoints']);
  });

  test('orders total, auto, then teleop ahead of the remaining components', () => {
    const model = buildCoprTableModel(
      {
        endgamePoints: { frc254: 12.2 },
        teleopPoints: { frc254: 55.2 },
        totalPoints: { frc254: 88.4 },
        autoPoints: { frc254: 21 },
      },
      2024,
    );

    expect(model.componentNames).toEqual([
      'totalPoints',
      'autoPoints',
      'teleopPoints',
      'endgamePoints',
    ]);
    expect(model.defaultVisible).toEqual({
      totalPoints: true,
      autoPoints: true,
      teleopPoints: true,
      endgamePoints: false,
    });
    expect(model.defaultSortComponent).toEqual('totalPoints');
  });

  test('uses the 2015 snake_case component names', () => {
    const model = buildCoprTableModel(
      {
        container_points: { frc254: 9 },
        teleop_points: { frc254: 55.2 },
        total_points: { frc254: 88.4 },
        auto_points: { frc254: 21 },
      },
      2015,
    );

    expect(model.componentNames.slice(0, 3)).toEqual([
      'total_points',
      'auto_points',
      'teleop_points',
    ]);
    expect(model.defaultVisible.container_points).toBe(false);
    expect(model.defaultSortComponent).toEqual('total_points');
  });

  test('uses the 2026 total-prefixed auto and teleop names', () => {
    const model = buildCoprTableModel(
      {
        totalTeleopPoints: { frc254: 55.2 },
        teleopPoints: { frc254: 55.2 },
        totalAutoPoints: { frc254: 21 },
        totalPoints: { frc254: 88.4 },
      },
      2026,
    );

    expect(model.componentNames.slice(0, 3)).toEqual([
      'totalPoints',
      'totalAutoPoints',
      'totalTeleopPoints',
    ]);
    expect(model.defaultVisible.teleopPoints).toBe(false);
  });

  test('falls back to the first three components when no default survives', () => {
    const model = buildCoprTableModel(
      {
        alpha: { frc254: 1 },
        beta: { frc254: 2 },
        gamma: { frc254: 3 },
        delta: { frc254: 4 },
      },
      2024,
    );

    expect(model.defaultVisible).toEqual({
      alpha: true,
      beta: true,
      gamma: true,
      delta: false,
    });
    expect(model.defaultSortComponent).toEqual('alpha');
  });

  test('never names a filtered-out component as the sort column', () => {
    const model = buildCoprTableModel(
      {
        totalPoints: { frc254: 0 },
        endgamePoints: { frc254: 12.2 },
      },
      2024,
    );

    expect(model.componentNames).toEqual(['endgamePoints']);
    expect(model.defaultSortComponent).toEqual('endgamePoints');
  });

  test('returns an empty model for empty input', () => {
    const model = buildCoprTableModel({}, 2024);

    expect(model.componentNames).toEqual([]);
    expect(model.rows).toEqual([]);
    expect(model.defaultVisible).toEqual({});
    expect(model.defaultSortComponent).toBeNull();
  });

  test('rows carry the union of team keys and omit missing values', () => {
    const model = buildCoprTableModel(
      {
        totalPoints: { frc254: 88.4, frc1678: 84.1 },
        endgamePoints: { frc254: 12.2, frc148: 9.9 },
      },
      2024,
    );

    expect(model.rows).toEqual([
      {
        teamKey: 'frc254',
        values: { totalPoints: 88.4, endgamePoints: 12.2 },
      },
      { teamKey: 'frc1678', values: { totalPoints: 84.1 } },
      { teamKey: 'frc148', values: { endgamePoints: 9.9 } },
    ]);
  });
});
