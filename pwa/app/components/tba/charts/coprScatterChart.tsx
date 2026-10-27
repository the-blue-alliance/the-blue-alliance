import { useMemo, useState } from 'react';
import {
  Cell,
  DefaultTooltipContentProps,
  DefaultZIndexes,
  Label,
  ReferenceLine,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZIndexLayer,
  usePlotArea,
  useXAxisScale,
  useYAxisScale,
} from 'recharts';
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent';
import { ScatterShapeProps } from 'recharts/types/util/ScatterUtils';

import HelpCircleIcon from '~icons/lucide/help-circle';

import { EventColors } from '~/api/colors';
import { EventCoprs } from '~/api/tba/read';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { ChartContainer } from '~/components/ui/chart';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import { parseColor, wcagContrast } from '~/lib/colorContrast';
import { useMediaQuery } from '~/lib/hooks';
import { Box, layoutLabels } from '~/lib/labelLayout';
import { camelCaseToHumanReadable, removeNonNumeric } from '~/lib/utils';

interface Datapoint {
  teamKey: string;
  valueX: number;
  valueY: number;
}

// Both axes set allowDataOverflow, which makes recharts clip the scatter layer
// to exactly the axis range. Pad the domain proportionally so the outermost
// dots and their labels sit inside that clip rather than straddling it.
const DOMAIN_PADDING_RATIO = 0.05;
const TARGET_TICKS = 5;

function niceStep(span: number): number {
  const rough = span / TARGET_TICKS;
  const power = 10 ** Math.floor(Math.log10(rough));
  const error = rough / power;
  const factor =
    error >= Math.sqrt(50)
      ? 10
      : error >= Math.sqrt(10)
        ? 5
        : error >= Math.SQRT2
          ? 2
          : 1;
  return factor * power;
}

function niceAxis(values: number[]) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding =
    (Math.max(max, 0) - Math.min(min, 0) || 1) * DOMAIN_PADDING_RATIO;
  const lo = min > 0 ? 0 : min - padding;
  const hi = max < 0 ? 0 : max + padding;
  const step = niceStep(hi - lo);
  const first = Math.ceil(lo / step);
  const ticks = Array.from(
    { length: Math.floor(hi / step) - first + 1 },
    (_, i) => Number(((first + i) * step).toPrecision(12)),
  );
  return { domain: [lo, hi] as [number, number], ticks };
}

const CARD_LIGHT = 'oklch(1 0 0)';
const CARD_DARK = 'oklch(0.287 0.004 286.09)';
const MIN_CONTRAST = 3;
const RING = 'var(--card-foreground)';
const GAP = 'var(--card)';
const NEUTRAL = 'var(--muted-foreground)';
const DOT_RADIUS = 5.5;
const HOVER_RADIUS = 14;
const HOVER_STEPS = 32;

function themed(light: string, dark: string): string {
  return light === dark ? light : `light-dark(${light}, ${dark})`;
}

function ringFor(fill: string, card: string): string {
  return wcagContrast(fill, card) < MIN_CONTRAST ? RING : GAP;
}

function outlineFor(fill: string, card: string): string {
  return wcagContrast(fill, card) < MIN_CONTRAST ? RING : 'transparent';
}

function getTeamPrimary(colors: EventColors, teamKey: string): string | null {
  const primaryHex =
    colors.teams[removeNonNumeric(teamKey)]?.colors?.primaryHex;
  return primaryHex ? parseColor(primaryHex) : null;
}

function getDotStyle(primary: string | null) {
  return primary
    ? {
        fill: primary,
        stroke: themed(
          ringFor(primary, CARD_LIGHT),
          ringFor(primary, CARD_DARK),
        ),
      }
    : { fill: NEUTRAL, stroke: GAP };
}

type Point = [number, number];

function keepCloserTo(
  polygon: Point[],
  [cx, cy]: Point,
  [ox, oy]: Point,
): Point[] {
  const side = ([x, y]: Point) =>
    (x - (cx + ox) / 2) * (ox - cx) + (y - (cy + oy) / 2) * (oy - cy);
  return polygon.flatMap((cur, i) => {
    const prev = polygon.at(i - 1) ?? cur;
    const sc = side(cur);
    const sp = side(prev);
    const t = sp / (sp - sc);
    const crossing: Point[] =
      sc <= 0 === sp <= 0
        ? []
        : [
            [
              prev[0] + t * (cur[0] - prev[0]),
              prev[1] + t * (cur[1] - prev[1]),
            ],
          ];
    return sc <= 0 ? [...crossing, cur] : crossing;
  });
}

function HoverArea({
  cx,
  cy,
  teamKey,
  data,
}: {
  cx: number;
  cy: number;
  teamKey: string;
  data: Datapoint[];
}) {
  const xScale = useXAxisScale();
  const yScale = useYAxisScale();
  const circle = Array.from({ length: HOVER_STEPS }, (_, i): Point => {
    const angle = (2 * Math.PI * i) / HOVER_STEPS;
    return [
      cx + HOVER_RADIUS * Math.cos(angle),
      cy + HOVER_RADIUS * Math.sin(angle),
    ];
  });
  const area = data
    .filter((d) => d.teamKey !== teamKey)
    .map((d): Point => [
      xScale?.(d.valueX) ?? Infinity,
      yScale?.(d.valueY) ?? Infinity,
    ])
    .filter(([x, y]) => Math.hypot(x - cx, y - cy) < 2 * HOVER_RADIUS)
    .reduce((polygon, other) => keepCloserTo(polygon, [cx, cy], other), circle);
  return (
    <polygon
      points={area.map((p) => p.join(',')).join(' ')}
      fill="transparent"
      data-testid={`hover-area-${teamKey}`}
    />
  );
}

function TeamDot({
  cx,
  cy,
  size,
  payload,
  fill,
  stroke,
  data,
}: ScatterShapeProps & {
  fill?: string;
  stroke?: string;
  data: Datapoint[];
}) {
  return (
    <g className="cursor-pointer">
      <HoverArea
        cx={cx ?? 0}
        cy={cy ?? 0}
        teamKey={(payload as Datapoint).teamKey}
        data={data}
      />
      <circle
        cx={cx}
        cy={cy}
        r={Math.sqrt(size / Math.PI)}
        pointerEvents="none"
        data-testid={`dot-${(payload as Datapoint).teamKey}`}
        style={{ fill, stroke, strokeWidth: 1.5 }}
      />
    </g>
  );
}

function chipSize(number: string) {
  return { w: number.length * 5.5 + 5, h: 11 };
}

function TeamChips({
  data,
  colors,
}: {
  data: Datapoint[];
  colors: EventColors;
}) {
  const xScale = useXAxisScale();
  const yScale = useYAxisScale();
  const plotArea = usePlotArea();
  const boxes = useMemo(() => {
    if (!xScale || !yScale || !plotArea) return [];
    return layoutLabels(
      data.map((d) => ({
        x: xScale(d.valueX) ?? 0,
        y: yScale(d.valueY) ?? 0,
        r: DOT_RADIUS,
        ...chipSize(d.teamKey.substring(3)),
      })),
      {
        x: plotArea.x,
        y: plotArea.y,
        w: plotArea.width,
        h: plotArea.height,
      },
    );
  }, [xScale, yScale, plotArea, data]);
  return (
    <ZIndexLayer zIndex={DefaultZIndexes.label}>
      {boxes.map((box, i) => (
        <TeamChip
          key={data[i].teamKey}
          box={box}
          number={data[i].teamKey.substring(3)}
          primary={getTeamPrimary(colors, data[i].teamKey)}
        />
      ))}
    </ZIndexLayer>
  );
}

function TeamChip({
  box,
  number,
  primary,
}: {
  box: Box;
  number: string;
  primary: string | null;
}) {
  const textColor = primary
    ? wcagContrast(primary, '#000000') >= wcagContrast(primary, '#ffffff')
      ? '#000000'
      : '#ffffff'
    : GAP;
  return (
    <g pointerEvents="none">
      <rect
        x={box.x}
        y={box.y}
        width={box.w}
        height={box.h}
        rx={3}
        style={{
          fill: primary ?? NEUTRAL,
          stroke: primary
            ? themed(
                outlineFor(primary, CARD_LIGHT),
                outlineFor(primary, CARD_DARK),
              )
            : 'transparent',
          strokeWidth: 1,
        }}
      />
      <text
        x={box.x + box.w / 2}
        y={box.y + box.h / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={9}
        fontWeight={600}
        style={{ fill: textColor }}
      >
        {number}
      </text>
    </g>
  );
}

export default function CoprScatterChart({
  coprs,
  colors,
  defaultXCopr,
  defaultYCopr,
}: {
  coprs: EventCoprs;
  colors: EventColors;
  defaultXCopr: string;
  defaultYCopr: string;
}) {
  const [selectedXCopr, setSelectedXCopr] = useState(defaultXCopr);
  const [selectedYCopr, setSelectedYCopr] = useState(defaultYCopr);
  const isDesktop = useMediaQuery('(min-width: 640px)');

  // Base UI's Select.Value renders the raw value unless the items are
  // registered on Select.Root, so provide value -> label pairs there too.
  const coprItems = Object.keys(coprs).map((k) => ({
    value: k,
    label: camelCaseToHumanReadable(k),
  }));

  const data: Datapoint[] = useMemo(
    () =>
      Object.keys(coprs[selectedXCopr])
        .map((tk) => ({
          teamKey: tk,
          valueX: coprs[selectedXCopr][tk],
          valueY: coprs[selectedYCopr][tk],
        }))
        .sort((a, b) => a.valueX - b.valueX),
    [selectedXCopr, selectedYCopr, coprs],
  );
  const xAxis = useMemo(() => niceAxis(data.map((d) => d.valueX)), [data]);
  const yAxis = useMemo(() => niceAxis(data.map((d) => d.valueY)), [data]);

  return (
    <Card>
      <CardHeader className="p-4 sm:p-6">
        <div className="flex justify-between">
          <div className="flex items-center gap-2">
            <CardTitle>Component OPRs</CardTitle>
            <Popover>
              <PopoverTrigger
                aria-label="How to submit team colors"
                openOnHover={isDesktop}
                className="rounded-sm text-muted-foreground
                  hover:text-foreground focus-visible:outline-2
                  focus-visible:outline-ring"
              >
                <HelpCircleIcon className="size-4" aria-hidden="true" />
              </PopoverTrigger>
              <PopoverContent align="start" className="text-sm">
                Team colors in this chart come from{' '}
                <a
                  href="https://frc-colors.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary underline"
                >
                  frc-colors
                </a>
                . To add or update your team’s colors, submit your team number
                and primary and secondary hex colors on{' '}
                <a
                  href="https://frc-colors.com/submit-colors"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary underline"
                >
                  frc-colors
                </a>
                .
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-1 pb-1 sm:px-6">
        <ChartContainer
          className="aspect-4/5 sm:aspect-video"
          config={{
            teamKey: { color: 'var(--primary)' },
            valueX: { label: selectedXCopr, color: 'var(--primary)' },
            valueY: { label: selectedYCopr, color: 'var(--primary)' },
            label: {
              color: 'var(--primary)',
            },
          }}
        >
          <ScatterChart
            data={data}
            margin={
              isDesktop
                ? { left: 20, right: 20, bottom: 20, top: 20 }
                : { left: 0, right: 10, bottom: 10, top: 10 }
            }
          >
            {xAxis.ticks.map((x) => (
              <ReferenceLine key={`gridline-x-${x}`} x={x} />
            ))}

            {yAxis.ticks.map((y) => (
              <ReferenceLine key={`gridline-y-${y}`} y={y} />
            ))}

            <XAxis
              dataKey="valueX"
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              type="number"
              domain={xAxis.domain}
              allowDataOverflow={true}
              ticks={xAxis.ticks}
            >
              <Label
                value={camelCaseToHumanReadable(selectedXCopr)}
                dy={isDesktop ? 17 : 10}
              />
            </XAxis>
            <YAxis
              dataKey="valueY"
              width={isDesktop ? 60 : 36}
              axisLine={false}
              tickLine={false}
              domain={yAxis.domain}
              allowDataOverflow={true}
              ticks={yAxis.ticks}
            >
              <Label
                value={camelCaseToHumanReadable(selectedYCopr)}
                angle={-90}
                dx={isDesktop ? -20 : -8}
              />
            </YAxis>
            <Tooltip
              content={
                <CustomTooltip
                  xCopr={camelCaseToHumanReadable(selectedXCopr)}
                  yCopr={camelCaseToHumanReadable(selectedYCopr)}
                />
              }
            />
            <Scatter shape={(props) => <TeamDot {...props} data={data} />}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  {...getDotStyle(getTeamPrimary(colors, entry.teamKey))}
                />
              ))}
            </Scatter>
            <TeamChips data={data} colors={colors} />
          </ScatterChart>
        </ChartContainer>
      </CardContent>
      <div
        className="flex flex-col gap-2 px-4 pb-4 sm:flex-row sm:justify-around
          sm:gap-4"
      >
        <div className="flex min-w-0 flex-row items-center gap-2">
          <div className="shrink-0 font-bold">Y Axis</div>
          <Select
            items={coprItems}
            value={selectedYCopr}
            onValueChange={(value) => value !== null && setSelectedYCopr(value)}
          >
            <SelectTrigger className="w-auto min-w-0 flex-1 sm:flex-none">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Y Axis</SelectLabel>
                {coprItems.map(({ value, label }) => (
                  <SelectItem value={value} key={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <div className="flex min-w-0 flex-row items-center gap-2">
          <div className="shrink-0 font-bold">X Axis</div>
          <Select
            items={coprItems}
            value={selectedXCopr}
            onValueChange={(value) => value !== null && setSelectedXCopr(value)}
          >
            <SelectTrigger className="w-auto min-w-0 flex-1 sm:flex-none">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>X Axis</SelectLabel>
                {coprItems.map(({ value, label }) => (
                  <SelectItem value={value} key={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>
      </div>
    </Card>
  );
}

function TooltipRow({ label, value }: { label: string; value?: ValueType }) {
  return (
    <div className="flex justify-between gap-4 leading-none">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono font-medium text-foreground numeric-data">
        {Number(value).toFixed(2)}
      </span>
    </div>
  );
}

const CustomTooltip = ({
  active,
  payload,
  xCopr,
  yCopr,
}: React.ComponentProps<typeof Tooltip> &
  Omit<
    DefaultTooltipContentProps<ValueType, NameType>,
    'accessibilityLayer'
  > & {
    xCopr: string;
    yCopr: string;
  }) => {
  if (active && payload && payload.length > 1) {
    const teamKey = (
      payload[0].payload as { teamKey: string }
    ).teamKey.substring(3);

    return (
      <div
        className="grid min-w-32 gap-1.5 rounded-lg border border-border/50
          bg-background px-2.5 py-1.5 text-xs shadow-xl"
      >
        <div className="font-medium">{teamKey}</div>
        <TooltipRow label={yCopr} value={payload[1].value} />
        <TooltipRow label={xCopr} value={payload[0].value} />
      </div>
    );
  }

  return null;
};
