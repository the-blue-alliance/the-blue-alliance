import { useMemo, useState } from 'react';
import {
  Cell,
  DefaultTooltipContentProps,
  Label,
  LabelList,
  ReferenceLine,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent';
import { Props as LabelProps } from 'recharts/types/component/Label';
import { ScatterShapeProps } from 'recharts/types/util/ScatterUtils';

import HelpCircleIcon from '~icons/lucide/help-circle';

import { EventColors, TeamColors } from '~/api/colors';
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
import { nudgeLightness, parseColor, wcagContrast } from '~/lib/colorContrast';
import { useMediaQuery } from '~/lib/hooks';
import { camelCaseToHumanReadable } from '~/lib/utils';

interface Datapoint {
  teamKey: string;
  valueX: number;
  valueY: number;
}

function generateWholeNumberedGridlinePoints(
  maxVal: number,
  increment: number,
) {
  return Array.from(
    { length: Math.ceil(maxVal / increment) + 1 },
    (_, i) => i * increment,
  );
}

function generateFractionalGridlinePoints(maxVal: number, segments: number) {
  const points = [];
  for (let i = 0; i <= segments; i++) {
    points.push(Math.round(i * (maxVal / segments) * 10) / 10);
  }
  return points;
}

function generateGridPoints(maxVal: number, segments: number) {
  return maxVal > 1
    ? generateWholeNumberedGridlinePoints(maxVal, Math.ceil(maxVal / segments))
    : generateFractionalGridlinePoints(maxVal, segments);
}

// Both axes set allowDataOverflow, which makes recharts clip the scatter layer
// to exactly the axis range. Pad the domain proportionally so the outermost
// dots and their labels sit inside that clip rather than straddling it.
const DOMAIN_PADDING_RATIO = 0.05;

function generateDomain(dataMin: number, dataMax: number): [number, number] {
  if (dataMax > 1) {
    const padding = (dataMax - Math.min(dataMin, 0)) * DOMAIN_PADDING_RATIO;

    return [
      dataMin > 0 ? 0 : Math.floor(dataMin - padding),
      Math.ceil(dataMax + padding),
    ];
  }

  return [-0.1, 1 + DOMAIN_PADDING_RATIO];
}

const TREATMENTS = {
  current: 'Current',
  adaptive: 'Adaptive ring',
  casing: 'Double ring',
  nudge: 'Lightness nudge',
  secondary: 'Secondary ring',
  chip: 'Team chips',
} as const;

type Treatment = keyof typeof TREATMENTS;

const treatmentItems = Object.entries(TREATMENTS).map(([value, label]) => ({
  value,
  label,
}));

const CARD_LIGHT = 'oklch(1 0 0)';
const CARD_DARK = 'oklch(0.287 0.004 286.09)';
const MIN_CONTRAST = 3;
const RING = 'var(--card-foreground)';
const GAP = 'var(--card)';
const NEUTRAL = 'var(--muted-foreground)';

interface DotStyle {
  fill: string;
  stroke: string;
  strokeWidth: number;
}

function themed(light: string, dark: string): string {
  return light === dark ? light : `light-dark(${light}, ${dark})`;
}

function ringFor(fill: string, card: string): string {
  return wcagContrast(fill, card) < MIN_CONTRAST ? RING : GAP;
}

function getTeamColors(
  colors: EventColors,
  teamKey: string,
): TeamColors | null {
  return colors.teams[teamKey.substring(3)]?.colors ?? null;
}

function getDotStyle(treatment: Treatment, team: TeamColors | null): DotStyle {
  const primary = team ? parseColor(team.primaryHex) : null;
  if (treatment === 'current') {
    return { fill: primary ?? NEUTRAL, stroke: RING, strokeWidth: 1 };
  }
  if (!primary) return { fill: NEUTRAL, stroke: GAP, strokeWidth: 1.5 };
  switch (treatment) {
    case 'casing':
      return { fill: primary, stroke: GAP, strokeWidth: 1.5 };
    case 'nudge': {
      const light = nudgeLightness(primary, CARD_LIGHT);
      const dark = nudgeLightness(primary, CARD_DARK);
      return {
        fill: themed(light, dark),
        stroke: themed(ringFor(light, CARD_LIGHT), ringFor(dark, CARD_DARK)),
        strokeWidth: 1.5,
      };
    }
    case 'secondary': {
      const secondary = parseColor(team?.secondaryHex ?? '');
      const ring = (card: string) =>
        secondary && wcagContrast(secondary, card) >= MIN_CONTRAST
          ? secondary
          : RING;
      return {
        fill: primary,
        stroke: themed(ring(CARD_LIGHT), ring(CARD_DARK)),
        strokeWidth: 2,
      };
    }
    default:
      return {
        fill: primary,
        stroke: themed(
          ringFor(primary, CARD_LIGHT),
          ringFor(primary, CARD_DARK),
        ),
        strokeWidth: 1.5,
      };
  }
}

function TeamDot({
  cx,
  cy,
  size,
  fill,
  stroke,
  strokeWidth,
  casing,
}: ScatterShapeProps & Partial<DotStyle> & { casing: boolean }) {
  const r = Math.sqrt(size / Math.PI);
  return (
    <g>
      {casing && <circle cx={cx} cy={cy} r={r + 2.5} style={{ fill: RING }} />}
      <circle
        cx={cx}
        cy={cy}
        r={casing ? r + 0.75 : r}
        style={{ fill, stroke, strokeWidth }}
      />
    </g>
  );
}

function TeamChip({
  viewBox,
  teamKey,
  team,
}: {
  viewBox: LabelProps['viewBox'];
  teamKey: string;
  team: TeamColors | null;
}) {
  if (!viewBox || !('width' in viewBox)) return null;
  const { x, y, width } = viewBox;
  const number = teamKey.substring(3);
  const primary = team ? parseColor(team.primaryHex) : null;
  const chipWidth = number.length * 6.5 + 8;
  const chipHeight = 14;
  const centerX = x + width / 2;
  const top = y - chipHeight - 3;
  const outline = (card: string) =>
    primary && wcagContrast(primary, card) < MIN_CONTRAST
      ? RING
      : 'transparent';
  const textColor = primary
    ? wcagContrast(primary, '#000000') >= wcagContrast(primary, '#ffffff')
      ? '#000000'
      : '#ffffff'
    : GAP;
  return (
    <g>
      <rect
        x={centerX - chipWidth / 2}
        y={top}
        width={chipWidth}
        height={chipHeight}
        rx={4}
        style={{
          fill: primary ?? NEUTRAL,
          stroke: themed(outline(CARD_LIGHT), outline(CARD_DARK)),
          strokeWidth: 1,
        }}
      />
      <text
        x={centerX}
        y={top + chipHeight / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={11}
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
  const [treatment, setTreatment] = useState<Treatment>('current');
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
            {generateGridPoints(
              Math.ceil(Math.max(...data.map((d) => d.valueX))),
              5,
            ).map((x) => (
              <ReferenceLine key={`gridline-x-${x}`} x={x} />
            ))}

            {generateGridPoints(
              Math.ceil(Math.max(...data.map((d) => d.valueY))),
              5,
            ).map((y) => (
              <ReferenceLine key={`gridline-y-${y}`} y={y} />
            ))}

            <XAxis
              dataKey="valueX"
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              type="number"
              domain={([dataMin, dataMax]) => generateDomain(dataMin, dataMax)}
              allowDataOverflow={true}
              ticks={generateGridPoints(
                Math.ceil(Math.max(...data.map((d) => d.valueX))),
                5,
              )}
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
              domain={([dataMin, dataMax]) => generateDomain(dataMin, dataMax)}
              allowDataOverflow={true}
              ticks={generateGridPoints(
                Math.ceil(Math.max(...data.map((d) => d.valueY))),
                5,
              )}
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
            <Scatter
              shape={(props: ScatterShapeProps) => (
                <TeamDot {...props} casing={treatment === 'casing'} />
              )}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  {...getDotStyle(
                    treatment,
                    getTeamColors(colors, entry.teamKey),
                  )}
                />
              ))}

              {treatment === 'current' ? (
                <LabelList
                  dataKey={'teamKey'}
                  position={'top'}
                  formatter={(value) => String(value).substring(3)}
                />
              ) : treatment === 'chip' ? (
                <LabelList
                  dataKey={'teamKey'}
                  content={({ viewBox, index }) => {
                    const teamKey = data[index ?? -1]?.teamKey;
                    return teamKey ? (
                      <TeamChip
                        viewBox={viewBox}
                        teamKey={teamKey}
                        team={getTeamColors(colors, teamKey)}
                      />
                    ) : null;
                  }}
                />
              ) : (
                <LabelList
                  dataKey={'teamKey'}
                  position={'top'}
                  formatter={(value) => String(value).substring(3)}
                  fill="var(--card-foreground)"
                  stroke="var(--card)"
                  strokeWidth={3}
                  strokeLinejoin="round"
                  paintOrder="stroke"
                />
              )}
            </Scatter>
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

        <div className="flex min-w-0 flex-row items-center gap-2">
          <div className="shrink-0 font-bold">Colors (temp)</div>
          <Select
            items={treatmentItems}
            value={treatment}
            onValueChange={(value) =>
              value !== null && setTreatment(value as Treatment)
            }
          >
            <SelectTrigger className="w-auto min-w-0 flex-1 sm:flex-none">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Colors</SelectLabel>
                {treatmentItems.map(({ value, label }) => (
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
        className="flex flex-col rounded-md bg-background text-foreground
          shadow-xl"
      >
        <div className="flex flex-col p-4">
          <div className="pb-2 text-xl">{teamKey}</div>
          <div className="">
            <div className="flex justify-between gap-4">
              <div>{yCopr}</div>
              <div>{Number(payload[1].value).toFixed(2)}</div>
            </div>
            <div className="flex justify-between gap-4">
              <div>{xCopr}</div>
              <div>{Number(payload[0].value).toFixed(2)}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};
