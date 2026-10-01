import { describe, expect, test } from 'vitest';

import { CmpQualificationMethod } from '~/api/tba/read';
import { CMP_QUALIFICATION_METHOD_LABELS } from '~/lib/api/CmpQualificationMethod';

describe('CMP_QUALIFICATION_METHOD_LABELS', () => {
  test('labels every qualification method the API defines', () => {
    const unlabeled = Object.values(CmpQualificationMethod).filter(
      (method) => !CMP_QUALIFICATION_METHOD_LABELS[method],
    );

    expect(unlabeled).toEqual([]);
  });

  test('spells out district points qualification', () => {
    expect(
      CMP_QUALIFICATION_METHOD_LABELS[CmpQualificationMethod.DISTRICT_POINTS],
    ).toBe('District Points');
  });
});
