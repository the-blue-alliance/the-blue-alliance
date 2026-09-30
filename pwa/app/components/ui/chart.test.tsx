import { render, screen } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartStyle,
  ChartTooltip,
  ChartTooltipContent,
} from '~/components/ui/chart';

// recharts' ResponsiveContainer only renders its children once it has
// measured a non-zero size, which jsdom never reports, so stand in for it.
vi.mock('recharts', async (importOriginal) => ({
  ...(await importOriginal<typeof import('recharts')>()),
  ResponsiveContainer: ({
    children,
    initialDimension,
  }: {
    children: React.ReactNode;
    initialDimension?: { width: number; height: number };
  }) => (
    <div
      data-testid="responsive-container"
      data-initial-width={initialDimension?.width}
    >
      {children}
    </div>
  ),
}));

function SquareIcon() {
  return <svg data-testid="icon" />;
}

const config: ChartConfig = {
  red: { label: 'Red alliance', color: '#ff0000', icon: SquareIcon },
  blue: {
    label: 'Blue alliance',
    theme: { light: '#0000ff', dark: '#8888ff' },
  },
  none: { label: 'Unstyled' },
};

type TooltipProps = ComponentProps<typeof ChartTooltipContent>;
type TooltipPayload = NonNullable<TooltipProps['payload']>;

function item(overrides: Record<string, unknown>): TooltipPayload[number] {
  return {
    name: 'red',
    dataKey: 'red',
    value: 42,
    color: '#ff0000',
    payload: {},
    ...overrides,
  } as unknown as TooltipPayload[number];
}

function renderInChart(children: React.ReactElement, chartConfig = config) {
  return render(
    <ChartContainer config={chartConfig}>{children}</ChartContainer>,
  );
}

describe('ChartContainer', () => {
  test('renders its children inside a responsive container with theme styles', () => {
    const { container } = renderInChart(<div>Chart body</div>);

    const chart = container.querySelector('[data-slot="chart"]');
    expect(chart?.getAttribute('data-chart')).toMatch(/^chart-/);
    expect(screen.getByText('Chart body')).toBeTruthy();
    expect(
      screen
        .getByTestId('responsive-container')
        .getAttribute('data-initial-width'),
    ).toBe('320');

    const style = chart?.querySelector('style');
    expect(style?.innerHTML).toContain('--color-red: #ff0000;');
    expect(style?.innerHTML).toContain('--color-blue: #0000ff;');
    expect(style?.innerHTML).toContain('.dark [data-chart=');
    expect(style?.innerHTML).toContain('--color-blue: #8888ff;');
    expect(style?.innerHTML).not.toContain('--color-none');
  });

  test('uses an explicit id and merges classes', () => {
    const { container } = render(
      <ChartContainer
        config={config}
        id="scores"
        className="group/chart"
        initialDimension={{ width: 100, height: 50 }}
      >
        <div>Body</div>
      </ChartContainer>,
    );

    const chart = container.querySelector('[data-slot="chart"]');
    expect(chart?.getAttribute('data-chart')).toBe('chart-scores');
    expect(chart?.className).toContain('group/chart');
    expect(
      screen
        .getByTestId('responsive-container')
        .getAttribute('data-initial-width'),
    ).toBe('100');
  });

  test('re-exports recharts tooltip and legend', () => {
    expect(ChartTooltip).toBeDefined();
    expect(ChartLegend).toBeDefined();
  });
});

describe('useChart', () => {
  test('tooltip and legend content throw outside a ChartContainer', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() => render(<ChartTooltipContent active payload={[]} />)).toThrow(
      'useChart must be used within a <ChartContainer />',
    );
  });
});

describe('ChartStyle', () => {
  test('renders nothing when no series has a color', () => {
    const { container } = render(
      <ChartStyle id="chart-x" config={{ none: { label: 'Unstyled' } }} />,
    );

    expect(container.innerHTML).toBe('');
  });

  test('skips themes a series does not define', () => {
    const { container } = render(
      <ChartStyle
        id="chart-x"
        config={{
          partial: {
            label: 'Partial',
            theme: { light: '#111111' } as unknown as {
              light: string;
              dark: string;
            },
          },
        }}
      />,
    );

    const css = container.querySelector('style')?.innerHTML ?? '';
    expect(css).toContain('--color-partial: #111111;');
    expect(css.match(/--color-partial/g)).toHaveLength(1);
  });
});

describe('ChartTooltipContent', () => {
  test('renders nothing when inactive or without payload', () => {
    const { container } = renderInChart(
      <ChartTooltipContent active={false} payload={[item({})]} />,
    );
    expect(container.querySelector('.shadow-xl')).toBeNull();

    const { container: empty } = renderInChart(
      <ChartTooltipContent active payload={[]} />,
    );
    expect(empty.querySelector('.shadow-xl')).toBeNull();
  });

  test('renders a dot indicator row with the config label and formatted value', () => {
    renderInChart(
      <ChartTooltipContent
        active
        payload={[item({ name: 'blue', dataKey: 'blue', value: 1234 })]}
        label="blue"
        className="group/tooltip"
        labelClassName="group/label"
      />,
    );

    // Heading label from config, then the series label in the row.
    const labels = screen.getAllByText('Blue alliance');
    expect(labels).toHaveLength(2);
    expect(labels[0].className).toContain('group/label');
    expect(screen.getByText('1,234')).toBeTruthy();
    expect(document.querySelector('.group\\/tooltip')).not.toBeNull();
    const indicator = document.querySelector('.h-2\\.5.w-2\\.5');
    expect(indicator).not.toBeNull();
    expect(
      (indicator as HTMLElement).style.getPropertyValue('--color-bg'),
    ).toBe('#ff0000');
  });

  test('renders the series icon instead of the indicator when configured', () => {
    renderInChart(
      <ChartTooltipContent active payload={[item({})]} label="red" />,
    );

    expect(screen.getByTestId('icon')).toBeTruthy();
    expect(document.querySelector('.h-2\\.5.w-2\\.5')).toBeNull();
  });

  test('hides the label and indicator when asked', () => {
    renderInChart(
      <ChartTooltipContent
        active
        hideLabel
        hideIndicator
        payload={[item({ name: 'blue', dataKey: 'blue' })]}
        label="blue"
      />,
    );

    expect(screen.getAllByText('Blue alliance')).toHaveLength(1);
    expect(document.querySelector('.h-2\\.5.w-2\\.5')).toBeNull();
  });

  test('nests the label next to the value for a single line indicator', () => {
    renderInChart(
      <ChartTooltipContent
        active
        indicator="line"
        payload={[item({ name: 'blue', dataKey: 'blue', value: 'n/a' })]}
        label="blue"
      />,
    );

    const grid = screen.getByText('n/a').previousElementSibling;
    expect(grid?.textContent).toBe('Blue allianceBlue alliance');
    expect(document.querySelector('.w-1')).not.toBeNull();
    expect(document.querySelector('.items-end')).not.toBeNull();
  });

  test('draws a dashed indicator with extra margin when nested', () => {
    renderInChart(
      <ChartTooltipContent
        active
        indicator="dashed"
        payload={[item({ name: 'blue', dataKey: 'blue', value: null })]}
        label="blue"
      />,
    );

    const indicator = document.querySelector('.border-dashed');
    expect(indicator?.className).toContain('my-0.5');
    expect(document.querySelector('.font-mono')).toBeNull();
  });

  test('uses labelFormatter, labelKey and an explicit color', () => {
    const labelFormatter = vi.fn<() => string>(() => 'Formatted');
    renderInChart(
      <ChartTooltipContent
        active
        payload={[item({ payload: { fill: '#00ff00' } })]}
        labelKey="red"
        labelFormatter={labelFormatter}
        color="#123456"
      />,
    );

    expect(labelFormatter).toHaveBeenCalledWith(
      'Red alliance',
      expect.any(Array),
    );
    expect(screen.getByText('Formatted')).toBeTruthy();
  });

  test('prefers the payload fill over the item color for the indicator', () => {
    renderInChart(
      <ChartTooltipContent
        active
        payload={[
          item({ name: 'blue', dataKey: 'blue', payload: { fill: '#00ff00' } }),
        ]}
        label={5}
      />,
    );

    const indicator = document.querySelector('.h-2\\.5.w-2\\.5') as HTMLElement;
    expect(indicator.style.getPropertyValue('--color-bg')).toBe('#00ff00');
    // A non-string label falls back to the series config label.
    expect(screen.getAllByText('Blue alliance')).toHaveLength(2);
  });

  test('delegates the row to a custom formatter', () => {
    const formatter = vi.fn<() => React.ReactNode>(() => (
      <span>Custom row</span>
    ));
    renderInChart(
      <ChartTooltipContent
        active
        payload={[item({})]}
        formatter={formatter}
        nameKey="series"
      />,
    );

    expect(formatter).toHaveBeenCalledWith(42, 'red', expect.anything(), 0, {});
    expect(screen.getByText('Custom row')).toBeTruthy();
  });

  test('falls back to the item name when it has no config entry', () => {
    renderInChart(
      <ChartTooltipContent
        active
        payload={[
          item({ name: 'unknown', dataKey: 'unknown', value: undefined }),
        ]}
        label="unknown"
        labelKey="unknown"
      />,
    );

    expect(screen.getByText('unknown')).toBeTruthy();
  });

  test('Bug #61: a string label with no config entry falls back to the raw label', () => {
    // Wrong today: `config[label].label` is read without optional chaining,
    // so a label that is not a config key throws a TypeError during render.
    // Correct: the tooltip renders and shows the raw label (upstream shadcn
    // guards this with `config[label]?.label || label`).
    renderInChart(
      <ChartTooltipContent active payload={[item({})]} label="missing" />,
    );

    expect(screen.getByText('missing')).toBeTruthy();
  });
});

describe('ChartLegendContent', () => {
  test('renders nothing without payload', () => {
    renderInChart(<ChartLegendContent payload={[]} />);
    expect(screen.getByTestId('responsive-container').innerHTML).toBe('');
  });

  test('renders icons or color swatches for each series', () => {
    renderInChart(
      <ChartLegendContent
        className="group/legend"
        payload={[
          { value: 'red', dataKey: 'red', color: '#ff0000' },
          { value: 'blue', dataKey: 'blue', color: '#0000ff' },
        ]}
      />,
    );

    const legend = document.querySelector('.group\\/legend') as HTMLElement;
    expect(legend.className).toContain('pt-3');
    expect(screen.getByTestId('icon')).toBeTruthy();
    expect(screen.getByText('Red alliance')).toBeTruthy();
    const swatch = screen.getByText('Blue alliance').querySelector('div');
    expect(swatch?.style.backgroundColor).toBe('rgb(0, 0, 255)');
  });

  test('can hide icons, sit above the chart and resolve names through nameKey', () => {
    renderInChart(
      <ChartLegendContent
        hideIcon
        verticalAlign="top"
        nameKey="series"
        payload={
          [
            {
              value: 'r',
              dataKey: 'x',
              color: '#ff0000',
              payload: { series: 'red' },
            },
            { value: 'b', dataKey: 'y', color: '#0000ff', series: 'blue' },
            // Exercises the non-object guard in getPayloadConfigFromPayload.
            'not-an-object',
          ] as unknown as ComponentProps<typeof ChartLegendContent>['payload']
        }
      />,
    );

    expect(document.querySelector('.pb-3')).not.toBeNull();
    expect(screen.queryByTestId('icon')).toBeNull();
    expect(screen.getByText('Red alliance')).toBeTruthy();
    expect(screen.getByText('Blue alliance')).toBeTruthy();
  });
});
