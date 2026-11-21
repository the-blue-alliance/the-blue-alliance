import { describe, expect, test } from 'vitest';

import { remapTeamKeys } from '~/lib/teamRemap';

describe('remapTeamKeys', () => {
  test.each([
    {
      name: 'replaces a remapped key',
      keys: ['frc9997', 'frc1073'],
      remapTeams: { frc9997: 'frc3467B' },
      expected: ['frc3467B', 'frc1073'],
    },
    {
      name: 'keeps keys that are not remapped',
      keys: ['frc254', 'frc1073'],
      remapTeams: { frc9997: 'frc3467B' },
      expected: ['frc254', 'frc1073'],
    },
    {
      name: 'returns the keys unchanged when remapTeams is null',
      keys: ['frc9997', 'frc1073'],
      remapTeams: null,
      expected: ['frc9997', 'frc1073'],
    },
    {
      name: 'drops the duplicate when old and new keys are both present',
      keys: ['frc9997', 'frc1073', 'frc1350', 'frc3467B'],
      remapTeams: { frc9997: 'frc3467B' },
      expected: ['frc3467B', 'frc1073', 'frc1350'],
    },
  ])('$name', ({ keys, remapTeams, expected }) => {
    expect(remapTeamKeys(keys, remapTeams)).toEqual(expected);
  });
});
