import { describe, expect, it } from 'vitest';

import { mean, percentile, stddev, summarize, summarizeRuns } from './stats';

describe('percentile', () => {
  it('returns NaN for an empty list', () => {
    expect(percentile([], 50)).toBeNaN();
  });

  it('returns the only value for a single-element list', () => {
    expect(percentile([42], 90)).toBe(42);
  });

  it('computes the median of an odd-length list', () => {
    expect(percentile([3, 1, 2], 50)).toBe(2);
  });

  it('interpolates between neighbours', () => {
    expect(percentile([0, 10], 50)).toBe(5);
    expect(percentile([0, 10, 20, 30], 90)).toBeCloseTo(27);
  });
});

describe('mean', () => {
  it('averages the values', () => {
    expect(mean([2, 4, 6])).toBe(4);
  });

  it('returns NaN for an empty list', () => {
    expect(mean([])).toBeNaN();
  });
});

describe('stddev', () => {
  it('is zero for fewer than two values', () => {
    expect(stddev([])).toBe(0);
    expect(stddev([5])).toBe(0);
  });

  it('computes the sample standard deviation', () => {
    expect(stddev([2, 4, 4, 4, 5, 5, 7, 9])).toBeCloseTo(2.13809, 4);
  });
});

describe('summarize', () => {
  it('reports every field', () => {
    expect(summarize([1, 2, 3, 4, 5])).toEqual({
      min: 1,
      median: 3,
      p90: 4.6,
      max: 5,
      mean: 3,
      stddev: expect.closeTo(1.5811, 3),
    });
  });
});

describe('summarizeRuns', () => {
  it('summarizes each metric key independently', () => {
    const result = summarizeRuns([
      { lcp: 100, cls: 0.1 },
      { lcp: 200, cls: 0.3 },
    ]);
    expect(result.lcp.median).toBe(150);
    expect(result.cls.max).toBeCloseTo(0.3);
  });
});
