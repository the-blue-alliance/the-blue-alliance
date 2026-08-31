import { describe, expect, test } from 'vitest';

import { formatSuccessRate, otherMatchLevel } from '~/lib/successRateUtils';

describe.concurrent('formatSuccessRate', () => {
  test('formats a rate to two decimal places', () => {
    expect(formatSuccessRate({ count: 17512, opportunities: 30352 })).toEqual(
      '57.70%',
    );
  });

  test('renders a dash rather than 0% when there were no opportunities', () => {
    expect(formatSuccessRate({ count: 0, opportunities: 0 })).toEqual('—');
  });

  test('handles the zero-count and perfect cases', () => {
    expect(formatSuccessRate({ count: 0, opportunities: 15176 })).toEqual(
      '0.00%',
    );
    expect(formatSuccessRate({ count: 90, opportunities: 90 })).toEqual(
      '100.00%',
    );
  });
});

describe.concurrent('otherMatchLevel', () => {
  test('swaps between the two match levels', () => {
    expect(otherMatchLevel('qual')).toEqual('playoff');
    expect(otherMatchLevel('playoff')).toEqual('qual');
  });
});
