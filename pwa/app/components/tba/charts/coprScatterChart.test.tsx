import { createEvent, fireEvent, render, screen } from '@testing-library/react';
import {
  type ReactElement,
  type ReactNode,
  cloneElement,
  isValidElement,
} from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import type { EventColors } from '~/api/colors';
import type { EventCoprs } from '~/api/tba/read';
import CoprScatterChart from '~/components/tba/charts/coprScatterChart';

type Domain = (range: [number, number]) => [number, number];

interface AxisProps {
  domain: Domain;
  ticks: number[];
  children?: ReactNode;
  width?: number;
}

// recharts renders nothing at jsdom's zero size, so stand in lightweight
// components that expose the props this chart computes.
const captured = vi.hoisted(() => ({
  margin: undefined as unknown,
  xAxis: undefined as AxisProps | undefined,
  yAxis: undefined as AxisProps | undefined,
  tooltip: undefined as ReactElement | undefined,
  formatter: undefined as ((value: unknown) => string) | undefined,
  isDesktop: true,
}));

vi.mock('recharts', () => ({
  ScatterChart: ({
    children,
    margin,
  }: {
    children: ReactNode;
    margin: unknown;
  }) => {
    captured.margin = margin;
    return <div>{children}</div>;
  },
  ReferenceLine: ({ x, y }: { x?: number; y?: number }) => (
    <span data-testid={x === undefined ? 'gridline-y' : 'gridline-x'}>
      {x ?? y}
    </span>
  ),
  XAxis: (props: AxisProps) => {
    captured.xAxis = props;
    return <div data-testid="x-axis">{props.children}</div>;
  },
  YAxis: (props: AxisProps) => {
    captured.yAxis = props;
    return <div data-testid="y-axis">{props.children}</div>;
  },
  Label: ({ value, dy, dx }: { value: string; dy?: number; dx?: number }) => (
    <span data-offset={dy ?? dx}>{value}</span>
  ),
  Tooltip: ({ content }: { content: ReactElement }) => {
    captured.tooltip = content;
    return null;
  },
  Scatter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Cell: ({ fill }: { fill?: string }) => (
    <span data-testid="cell" data-fill={fill ?? 'none'} />
  ),
  LabelList: ({ formatter }: { formatter: (value: unknown) => string }) => {
    captured.formatter = formatter;
    return null;
  },
}));

vi.mock('~/components/ui/chart', () => ({
  ChartContainer: ({ children }: { children: ReactNode }) => (
    <div>{children}</div>
  ),
}));

vi.mock('~/lib/hooks', () => ({
  useMediaQuery: () => captured.isDesktop,
}));

const COPRS: EventCoprs = {
  totalPoints: { frc254: 47.2, frc1678: 12.4, frc604: -3.1 },
  autoMobility: { frc254: 0.9, frc1678: 0.5, frc604: 0.1 },
};

function makeColors(): EventColors {
  return {
    teams: {
      '254': {
        teamNumber: 254,
        colors: { verified: true, primaryHex: '#0000ff', secondaryHex: '#fff' },
      },
      '1678': {
        teamNumber: 1678,
        colors: { verified: true, primaryHex: '#ffffff', secondaryHex: '#0f0' },
      },
    },
  };
}

function renderChart(colors = makeColors()) {
  render(
    <CoprScatterChart
      coprs={COPRS}
      colors={colors}
      defaultXCopr="totalPoints"
      defaultYCopr="autoMobility"
    />,
  );
  return colors;
}

function textsOf(testId: string) {
  return screen.getAllByTestId(testId).map((el) => el.textContent);
}

function choose(option: HTMLElement) {
  fireEvent.pointerMove(option, { pointerType: 'mouse' });
  fireEvent.pointerDown(option, { pointerType: 'mouse', button: 0 });
  fireEvent.mouseDown(option, { button: 0 });
  fireEvent.pointerUp(option, { pointerType: 'mouse', button: 0 });
  fireEvent.mouseUp(option, { button: 0 });
  fireEvent.click(option, { button: 0 });
}

function axis(which: 'xAxis' | 'yAxis') {
  const props = captured[which];
  if (!props) throw new Error(`${which} was not rendered`);
  return props;
}

describe('CoprScatterChart', () => {
  beforeEach(() => {
    captured.isDesktop = true;
  });

  test('explains how to submit team colors on desktop hover', async () => {
    renderChart();

    const trigger = screen.getByRole('button', {
      name: 'How to submit team colors',
    });
    const pointerEnter = createEvent.pointerOver(trigger);
    Object.defineProperty(pointerEnter, 'pointerType', { value: 'mouse' });
    fireEvent(trigger, pointerEnter);
    fireEvent.mouseEnter(trigger);
    fireEvent.mouseMove(trigger);

    expect(
      await screen.findByText(
        /submit your team number and primary and secondary hex colors/,
      ),
    ).toBeTruthy();
  });

  test('explains how to submit team colors on mobile tap', async () => {
    captured.isDesktop = false;
    renderChart();

    fireEvent.click(
      screen.getByRole('button', { name: 'How to submit team colors' }),
    );

    expect(
      await screen.findByText(
        /submit your team number and primary and secondary hex colors/,
      ),
    ).toBeTruthy();
  });

  test.each([
    ['homepage', 0, 'https://frc-colors.com'],
    ['submission form', 1, 'https://frc-colors.com/submit-colors'],
  ])(
    'links to the frc-colors %s when help is opened',
    async (_name, index, href) => {
      renderChart();

      fireEvent.click(
        screen.getByRole('button', { name: 'How to submit team colors' }),
      );

      expect(
        (await screen.findAllByRole('link', { name: 'frc-colors' }))[
          index
        ].getAttribute('href'),
      ).toBe(href);
    },
  );

  test('labels the axes with human-readable COPR names', () => {
    renderChart();

    expect(screen.getByText('Component OPRs')).toBeTruthy();
    expect(
      screen.getByTestId('x-axis').querySelector('span')?.textContent,
    ).toBe('Total Points');
    expect(
      screen.getByTestId('y-axis').querySelector('span')?.textContent,
    ).toBe('Auto Mobility');
  });

  test('uses whole-number gridlines above 1 and tenths below', () => {
    renderChart();

    expect(textsOf('gridline-x')).toEqual(['0', '10', '20', '30', '40', '50']);
    expect(textsOf('gridline-y')).toEqual([
      '0',
      '0.2',
      '0.4',
      '0.6',
      '0.8',
      '1',
    ]);
    expect(axis('xAxis').ticks).toEqual([0, 10, 20, 30, 40, 50]);
    expect(axis('yAxis').ticks).toEqual([0, 0.2, 0.4, 0.6, 0.8, 1]);
  });

  test('pads the axis domain around the data', () => {
    renderChart();
    const { domain } = axis('xAxis');

    expect(domain([5, 40])).toEqual([0, 42]);
    expect(domain([-3.1, 47.2])).toEqual([-6, 50]);
    expect(domain([0.1, 0.9])).toEqual([-0.1, 1.05]);
    expect(axis('yAxis').domain([0.1, 0.9])).toEqual([-0.1, 1.05]);
  });

  test("fills each dot with its team's primary color", () => {
    renderChart();

    // Sorted by X value: frc604, frc1678, frc254.
    expect(screen.getAllByTestId('cell')[2].dataset.fill).toBe('#0000ff');
  });

  test('keeps a white team color instead of darkening it', () => {
    renderChart();

    expect(screen.getAllByTestId('cell')[1].dataset.fill).toBe('#ffffff');
  });

  test('fills dots for teams missing from the colors data with the theme primary', () => {
    renderChart();

    expect(screen.getAllByTestId('cell')[0].dataset.fill).toBe(
      'hsl(var(--primary))',
    );
  });

  test('does not mutate the passed-in colors', () => {
    // The passed-in colors are typically React Query cache data.
    const colors = renderChart();

    expect(colors).toEqual(makeColors());
  });

  test('leaves dots unfilled for teams with no colors on record', () => {
    const colors = makeColors();
    colors.teams['254'].colors = null;
    renderChart(colors);

    expect(screen.getAllByTestId('cell')[2].dataset.fill).toBe('none');
  });

  test('labels dots with the team number', () => {
    renderChart();

    expect(captured.formatter?.('frc254')).toBe('254');
  });

  test('uses tighter spacing on small screens', () => {
    captured.isDesktop = false;
    renderChart();

    expect(captured.margin).toEqual({
      left: 0,
      right: 10,
      bottom: 10,
      top: 10,
    });
    expect(axis('yAxis').width).toBe(36);
    expect(
      screen.getByTestId('x-axis').querySelector('span')?.dataset.offset,
    ).toBe('10');
  });

  test('uses roomier spacing on desktop', () => {
    renderChart();

    expect(captured.margin).toEqual({
      left: 20,
      right: 20,
      bottom: 20,
      top: 20,
    });
    expect(axis('yAxis').width).toBe(60);
  });

  test('shows both values in the tooltip for a hovered team', () => {
    renderChart();
    const tooltip = captured.tooltip;
    if (!isValidElement(tooltip)) throw new Error('No tooltip');

    render(
      cloneElement(tooltip, {
        active: true,
        payload: [
          { value: 47.2, payload: { teamKey: 'frc254' } },
          { value: 0.9 },
        ],
      } as object),
    );

    expect(screen.getByText('254')).toBeTruthy();
    expect(screen.getByText('47.20')).toBeTruthy();
    expect(screen.getByText('0.90')).toBeTruthy();
  });

  test('renders no tooltip when inactive or incomplete', () => {
    renderChart();
    const tooltip = captured.tooltip;
    if (!isValidElement(tooltip)) throw new Error('No tooltip');

    const inactive = render(cloneElement(tooltip, { active: false } as object));
    expect(inactive.container.innerHTML).toBe('');
    const partial = render(
      cloneElement(tooltip, {
        active: true,
        payload: [{ value: 1, payload: { teamKey: 'frc254' } }],
      } as object),
    );
    expect(partial.container.innerHTML).toBe('');
  });

  test('switches the plotted COPRs', async () => {
    renderChart();

    const [yTrigger, xTrigger] = screen.getAllByRole('combobox');
    fireEvent.click(xTrigger);
    choose(await screen.findByRole('option', { name: 'Auto Mobility' }));

    expect(axis('xAxis').ticks).toEqual([0, 0.2, 0.4, 0.6, 0.8, 1]);

    fireEvent.click(yTrigger);
    choose(await screen.findByRole('option', { name: 'Total Points' }));

    expect(axis('yAxis').ticks).toEqual([0, 10, 20, 30, 40, 50]);
  });
});
