import { act, render, screen, waitFor } from '@testing-library/react';
import { type MutableRefObject, useRef } from 'react';
import { describe, expect, test, vi } from 'vitest';

import { AllianceColor, type Match } from '~/api/tba/read';
import {
  type AdvancementPath,
  EliminationBracketPaths,
  type PlayoffMatchHandle,
  type SeriesResult,
  type WinnerLink,
  useAdvancementPaths,
} from '~/components/tba/eliminationBracketPaths';

interface Rect {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** Fake `getBoundingClientRect` driven by a `data-rect` JSON attribute. */
function mockBoundingRects() {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(
    function (this: HTMLElement) {
      const raw = this.dataset.rect;
      const rect: Rect = raw
        ? (JSON.parse(raw) as Rect)
        : { left: 0, top: 0, width: 0, height: 0 };
      return {
        x: rect.left,
        y: rect.top,
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        right: rect.left + rect.width,
        bottom: rect.top + rect.height,
        toJSON: () => rect,
      };
    },
  );
}

function element(rect: Rect): HTMLDivElement {
  const el = document.createElement('div');
  el.dataset.rect = JSON.stringify(rect);
  return el;
}

function handle(
  overrides: Partial<PlayoffMatchHandle> = {},
): PlayoffMatchHandle {
  return {
    card: element({ left: 0, top: 0, width: 100, height: 60 }),
    redRow: element({ left: 0, top: 0, width: 100, height: 30 }),
    blueRow: element({ left: 0, top: 30, width: 100, height: 30 }),
    redAlliance: null,
    blueAlliance: null,
    ...overrides,
  };
}

function seriesResult(overrides: Partial<SeriesResult>): SeriesResult {
  return {
    redTeams: [],
    blueTeams: [],
    redAllianceNumber: 1,
    blueAllianceNumber: 8,
    redResults: [],
    blueResults: [],
    redWon: false,
    blueWon: false,
    matchRedTeams: [],
    matchBlueTeams: [],
    ...overrides,
  };
}

/** Keys the fake match list on its first match key so results can be looked up. */
function matchesFor(key: string): Match[] {
  return [{ key } as Match];
}

function Harness({
  handles,
  winnerLinks,
  matchLookup,
  results,
  containerRect,
  attachContainer = true,
}: {
  handles: Record<string, PlayoffMatchHandle | null>;
  winnerLinks: WinnerLink[];
  matchLookup: Record<string, Match[] | undefined>;
  results: Record<string, SeriesResult | null>;
  containerRect: Rect;
  attachContainer?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const matchRefs: MutableRefObject<Record<string, PlayoffMatchHandle | null>> =
    useRef(handles);
  const { paths, svgSize } = useAdvancementPaths({
    containerRef,
    matchRefs,
    winnerLinks,
    matchLookup,
    getSeriesResult: (matches) =>
      matches ? (results[matches[0].key] ?? null) : null,
  });

  return (
    <div
      ref={attachContainer ? containerRef : undefined}
      data-rect={JSON.stringify(containerRect)}
    >
      <output data-testid="size">{`${svgSize.width}x${svgSize.height}`}</output>
      <output data-testid="paths">{JSON.stringify(paths)}</output>
    </div>
  );
}

const containerRect: Rect = { left: 10, top: 20, width: 500, height: 300 };

function readPaths(): AdvancementPath[] {
  return JSON.parse(
    screen.getByTestId('paths').textContent ?? '[]',
  ) as AdvancementPath[];
}

describe('useAdvancementPaths', () => {
  test('draws a curve from the winning row to the matching row of the next match', async () => {
    mockBoundingRects();
    const from = handle({
      redRow: element({ left: 110, top: 120, width: 100, height: 30 }),
    });
    const to = handle({
      redAlliance: 1,
      redRow: element({ left: 310, top: 220, width: 100, height: 30 }),
    });

    render(
      <Harness
        handles={{ A: from, B: to }}
        winnerLinks={[{ from: 'A', to: 'B' }]}
        matchLookup={{ A: matchesFor('A') }}
        results={{ A: seriesResult({ redWon: true }) }}
        containerRect={containerRect}
      />,
    );

    await waitFor(() => expect(readPaths()).toHaveLength(1));
    const path = readPaths()[0];
    expect(path.winner).toBe(AllianceColor.RED);
    expect(path.allianceNumber).toBe(1);
    expect(path.key).toBe('A-B');
    // start: right edge of red row (210) - container left (10), centre y 135 - 20
    // end: left edge of target row (310) - 10, centre y 235 - 20
    expect(path.d).toBe('M 200 115 C 232 115 268 215 300 215');
    expect(screen.getByTestId('size').textContent).toBe('500x300');
  });

  test('uses the blue row when blue won and lands on the blue row of the next match', async () => {
    mockBoundingRects();
    const from = handle({
      blueRow: element({ left: 0, top: 100, width: 100, height: 20 }),
    });
    const to = handle({
      blueAlliance: 8,
      blueRow: element({ left: 200, top: 300, width: 100, height: 20 }),
    });

    render(
      <Harness
        handles={{ A: from, B: to }}
        winnerLinks={[{ from: 'A', to: 'B' }]}
        matchLookup={{ A: matchesFor('A') }}
        results={{ A: seriesResult({ blueWon: true }) }}
        containerRect={{ left: 0, top: 0, width: 400, height: 400 }}
      />,
    );

    await waitFor(() => expect(readPaths()).toHaveLength(1));
    const path = readPaths()[0];
    expect(path.winner).toBe(AllianceColor.BLUE);
    expect(path.allianceNumber).toBe(8);
    expect(path.d).toBe('M 100 110 C 132 110 168 310 200 310');
  });

  test('falls back to the card rectangles when rows are missing or unmatched', async () => {
    mockBoundingRects();
    const from = handle({
      redRow: null,
      card: element({ left: 0, top: 0, width: 100, height: 100 }),
    });
    // Neither side of the target holds alliance 1, so the whole card is used.
    const to = handle({
      redAlliance: 2,
      blueAlliance: 3,
      card: element({ left: 200, top: 0, width: 100, height: 100 }),
    });

    render(
      <Harness
        handles={{ A: from, B: to }}
        winnerLinks={[{ from: 'A', to: 'B' }]}
        matchLookup={{ A: matchesFor('A') }}
        results={{ A: seriesResult({ redWon: true }) }}
        containerRect={{ left: 0, top: 0, width: 400, height: 400 }}
      />,
    );

    await waitFor(() => expect(readPaths()).toHaveLength(1));
    expect(readPaths()[0].d).toBe('M 100 50 C 132 50 168 50 200 50');
  });

  test('skips links whose series has no winner, no result, or missing nodes', async () => {
    mockBoundingRects();
    render(
      <Harness
        handles={{
          A: handle(),
          B: handle({ redAlliance: 1 }),
          C: handle(),
          D: handle(),
          E: handle(),
          F: handle({ redRow: null, card: null }),
          G: handle({ card: null, redRow: null, blueRow: null }),
        }}
        winnerLinks={[
          // Missing destination node.
          { from: 'A', to: 'missing' },
          // No matches for this series.
          { from: 'C', to: 'B' },
          // Series has no result.
          { from: 'D', to: 'B' },
          // Series is unfinished.
          { from: 'E', to: 'B' },
          // Winner without an alliance number cannot be linked.
          { from: 'A', to: 'B' },
          // Winning row and card are both unavailable.
          { from: 'F', to: 'B' },
          // Target has no row for the winner and no card.
          { from: 'B', to: 'G' },
        ]}
        matchLookup={{
          A: matchesFor('A'),
          B: matchesFor('B'),
          D: matchesFor('D'),
          E: matchesFor('E'),
          F: matchesFor('F'),
        }}
        results={{
          A: seriesResult({ redWon: true, redAllianceNumber: null }),
          B: seriesResult({ redWon: true, redAllianceNumber: 1 }),
          D: null,
          E: seriesResult({}),
          F: seriesResult({ redWon: true }),
        }}
        containerRect={containerRect}
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId('size').textContent).toBe('500x300'),
    );
    expect(readPaths()).toEqual([]);
  });

  test('clears paths when there is no container', async () => {
    mockBoundingRects();
    render(
      <Harness
        handles={{ A: handle(), B: handle({ redAlliance: 1 }) }}
        winnerLinks={[{ from: 'A', to: 'B' }]}
        matchLookup={{ A: matchesFor('A') }}
        results={{ A: seriesResult({ redWon: true }) }}
        containerRect={containerRect}
        attachContainer={false}
      />,
    );

    await act(
      () =>
        new Promise<void>((resolve) => requestAnimationFrame(() => resolve())),
    );
    expect(readPaths()).toEqual([]);
    expect(screen.getByTestId('size').textContent).toBe('0x0');
  });

  test('recomputes on window resize and stops listening after unmount', async () => {
    mockBoundingRects();
    const addSpy = vi.spyOn(window, 'addEventListener');
    const removeSpy = vi.spyOn(window, 'removeEventListener');
    const from = handle();
    const to = handle({ redAlliance: 1 });

    const { unmount } = render(
      <Harness
        handles={{ A: from, B: to }}
        winnerLinks={[{ from: 'A', to: 'B' }]}
        matchLookup={{ A: matchesFor('A') }}
        results={{ A: seriesResult({ redWon: true }) }}
        containerRect={containerRect}
      />,
    );

    await waitFor(() => expect(readPaths()).toHaveLength(1));
    const firstD = readPaths()[0].d;

    // Move the target and fire a resize; the curve should follow it.
    to.redRow = element({ left: 400, top: 0, width: 100, height: 30 });
    act(() => {
      window.dispatchEvent(new Event('resize'));
    });
    await waitFor(() => expect(readPaths()[0].d).not.toBe(firstD));

    const resizeHandler = addSpy.mock.calls.find(
      ([type]) => type === 'resize',
    )?.[1];
    expect(resizeHandler).toBeDefined();
    unmount();
    expect(removeSpy).toHaveBeenCalledWith('resize', resizeHandler);
  });
});

describe('EliminationBracketPaths', () => {
  const paths: AdvancementPath[] = [
    {
      d: 'M 0 0 C 1 1 2 2 3 3',
      winner: AllianceColor.RED,
      allianceNumber: 1,
      key: 'a',
    },
    {
      d: 'M 4 4 C 5 5 6 6 7 7',
      winner: AllianceColor.BLUE,
      allianceNumber: 2,
      key: 'b',
    },
  ];

  test('renders nothing until the container has a size', () => {
    const { container } = render(
      <EliminationBracketPaths
        paths={paths}
        svgSize={{ width: 0, height: 100 }}
        hoveredAlliance={null}
      />,
    );
    expect(container.innerHTML).toBe('');

    const { container: noHeight } = render(
      <EliminationBracketPaths
        paths={paths}
        svgSize={{ width: 100, height: 0 }}
        hoveredAlliance={null}
      />,
    );
    expect(noHeight.innerHTML).toBe('');
  });

  test('draws every path in its alliance colour', () => {
    const { container } = render(
      <EliminationBracketPaths
        paths={paths}
        svgSize={{ width: 300, height: 200 }}
        hoveredAlliance={null}
      />,
    );

    const svg = container.querySelector('svg');
    expect(svg?.getAttribute('viewBox')).toBe('0 0 300 200');
    const drawn = container.querySelectorAll('path');
    expect(drawn).toHaveLength(2);
    expect(drawn[0].getAttribute('stroke')).toBe('var(--alliance-red-accent)');
    expect(drawn[0].getAttribute('stroke-width')).toBe('3');
    expect(drawn[0].getAttribute('stroke-opacity')).toBe('0.6');
    expect(drawn[0].style.filter).toBe('none');
    expect(drawn[1].getAttribute('stroke')).toBe('var(--alliance-blue-accent)');
  });

  test('emphasises the hovered alliance path', () => {
    const { container } = render(
      <EliminationBracketPaths
        paths={paths}
        svgSize={{ width: 300, height: 200 }}
        hoveredAlliance={2}
      />,
    );

    const drawn = container.querySelectorAll('path');
    expect(drawn[0].getAttribute('stroke-width')).toBe('3');
    expect(drawn[1].getAttribute('stroke-width')).toBe('4');
    expect(drawn[1].getAttribute('stroke-opacity')).toBe('1');
    expect(drawn[1].style.filter).toContain('drop-shadow');
  });
});
