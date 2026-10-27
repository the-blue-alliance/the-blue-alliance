import { describe, expect, test } from 'vitest';

import { type Box, layoutLabels } from '~/lib/labelLayout';

const BOUNDS: Box = { x: 0, y: 0, w: 200, h: 200 };

function overlaps(a: Box, b: Box): boolean {
  return (
    a.x < b.x + b.w && b.x < a.x + a.w && a.y < b.y + b.h && b.y < a.y + a.h
  );
}

describe('layoutLabels', () => {
  test('centers a lone label above its dot', () => {
    const [label] = layoutLabels(
      [{ x: 100, y: 100, r: 5, w: 20, h: 10 }],
      BOUNDS,
    );

    expect(label).toEqual({ x: 90, y: 83, w: 20, h: 10 });
  });

  test('separates labels whose dots sit side by side', () => {
    const [left, right] = layoutLabels(
      [
        { x: 100, y: 100, r: 5, w: 20, h: 10 },
        { x: 110, y: 100, r: 5, w: 20, h: 10 },
      ],
      BOUNDS,
    );

    expect(overlaps(left, right)).toBe(false);
  });

  test('moves a label off a neighboring dot', () => {
    const [label] = layoutLabels(
      [
        { x: 100, y: 100, r: 5, w: 20, h: 10 },
        { x: 97, y: 88, r: 5, w: 20, h: 10 },
      ],
      BOUNDS,
    );

    expect(overlaps(label, { x: 92, y: 83, w: 10, h: 10 })).toBe(false);
  });

  test('keeps a label inside the plot when its dot touches the top edge', () => {
    const [label] = layoutLabels(
      [{ x: 100, y: 3, r: 5, w: 20, h: 10 }],
      BOUNDS,
    );

    expect(label.y).toBeGreaterThanOrEqual(0);
  });

  test('returns the same layout every time for the same dots', () => {
    const anchors = [
      { x: 100, y: 100, r: 5, w: 20, h: 10 },
      { x: 110, y: 100, r: 5, w: 20, h: 10 },
      { x: 105, y: 90, r: 5, w: 20, h: 10 },
    ];

    expect(layoutLabels(anchors, BOUNDS)).toEqual(
      layoutLabels(anchors, BOUNDS),
    );
  });
});
