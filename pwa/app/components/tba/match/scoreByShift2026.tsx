import { useState } from 'react';
import {
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  XAxis,
  YAxis,
} from 'recharts';

import { Match, MatchScoreBreakdown2026 } from '~/api/tba/read';
import {
  type ChartConfig,
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from '~/components/ui/chart';
import { Checkbox } from '~/components/ui/checkbox';

interface ShiftScore {
  shift: string;
  red: number;
  blue: number;
}

const RED_COLOR = '#ef4444';
const BLUE_COLOR = '#3b82f6';

function makeChartConfig(match: Match): ChartConfig {
  const redLabel = match.alliances.red.team_keys
    .map((k) => k.substring(3))
    .join('-');
  const blueLabel = match.alliances.blue.team_keys
    .map((k) => k.substring(3))
    .join('-');
  return {
    red: { label: redLabel, color: RED_COLOR },
    blue: { label: blueLabel, color: BLUE_COLOR },
  };
}

// Red is above when red >= blue; blue is above when blue > red.
// This guarantees the two labels always end up on opposite sides.
function makeLabel(alliance: 'red' | 'blue', data: ShiftScore[]) {
  const fill = alliance === 'red' ? RED_COLOR : BLUE_COLOR;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return function ShiftLabel(props: any) {
    const { x, y, value, index } = props as {
      x?: number;
      y?: number;
      value?: number;
      index?: number;
    };
    if (
      value == null ||
      x == null ||
      y == null ||
      index == null ||
      index >= data.length
    )
      return null;
    const point = data[index];
    const isAbove =
      alliance === 'red' ? point.red >= point.blue : point.blue > point.red;
    const dy = isAbove ? -10 : 18;
    return (
      <text
        x={Number(x)}
        y={Number(y) + dy}
        textAnchor="middle"
        fill={fill}
        fontSize={11}
        fontWeight={600}
      >
        {value}
      </text>
    );
  };
}

function buildShiftData(
  scoreBreakdown: MatchScoreBreakdown2026,
  activeOnly: boolean,
): ShiftScore[] {
  const { red, blue } = scoreBreakdown;

  const redAuto = red.totalAutoPoints;
  const blueAuto = blue.totalAutoPoints;
  const redTrans = redAuto + red.hubScore.transitionPoints;
  const blueTrans = blueAuto + blue.hubScore.transitionPoints;
  const redShift1 = redTrans + red.hubScore.shift1Points;
  const blueShift1 = blueTrans + blue.hubScore.shift1Points;
  const redShift2 = redShift1 + red.hubScore.shift2Points;
  const blueShift2 = blueShift1 + blue.hubScore.shift2Points;
  const redShift3 = redShift2 + red.hubScore.shift3Points;
  const blueShift3 = blueShift2 + blue.hubScore.shift3Points;
  const redShift4 = redShift3 + red.hubScore.shift4Points;
  const blueShift4 = blueShift3 + blue.hubScore.shift4Points;

  if (activeOnly) {
    return [
      { shift: 'Auto', red: redAuto, blue: blueAuto },
      { shift: 'Trans', red: redTrans, blue: blueTrans },
      { shift: 'First', red: redShift2, blue: blueShift2 },
      { shift: 'Second', red: redShift4, blue: blueShift4 },
      { shift: 'Endgame', red: red.totalPoints, blue: blue.totalPoints },
    ];
  }

  return [
    { shift: 'Auto', red: redAuto, blue: blueAuto },
    { shift: 'Trans', red: redTrans, blue: blueTrans },
    { shift: 'Shift 1', red: redShift1, blue: blueShift1 },
    { shift: 'Shift 2', red: redShift2, blue: blueShift2 },
    { shift: 'Shift 3', red: redShift3, blue: blueShift3 },
    { shift: 'Shift 4', red: redShift4, blue: blueShift4 },
    { shift: 'Endgame', red: red.totalPoints, blue: blue.totalPoints },
  ];
}

export default function ScoreByShift2026({
  scoreBreakdown,
  match,
}: {
  scoreBreakdown: MatchScoreBreakdown2026;
  match: Match;
}) {
  const [activeOnly, setActiveOnly] = useState(false);
  const data = buildShiftData(scoreBreakdown, activeOnly);
  const chartConfig = makeChartConfig(match);
  const RedLabel = makeLabel('red', data);
  const BlueLabel = makeLabel('blue', data);

  return (
    <div className="rounded-lg border bg-card p-3">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Score by Shift</h3>
        <label
          htmlFor="active-only-toggle"
          className="flex cursor-pointer items-center gap-1.5 text-xs"
        >
          <Checkbox
            id="active-only-toggle"
            checked={activeOnly}
            onCheckedChange={(checked) => setActiveOnly(checked === true)}
          />
          <span>Active periods only</span>
        </label>
      </div>
      <ChartContainer config={chartConfig}>
        <LineChart
          data={data}
          margin={{ top: 24, right: 20, left: 20, bottom: 0 }}
        >
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey="shift"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 11 }}
          />
          <YAxis hide />
          <ChartTooltip
            content={
              <ChartTooltipContent hideLabel className="min-w-[11rem]" />
            }
          />
          <Line
            dataKey="red"
            stroke="var(--color-red)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-red)', r: 4 }}
            activeDot={{ r: 6 }}
            type="linear"
          >
            <LabelList dataKey="red" content={RedLabel} />
          </Line>
          <Line
            dataKey="blue"
            stroke="var(--color-blue)"
            strokeWidth={2}
            dot={{ fill: 'var(--color-blue)', r: 4 }}
            activeDot={{ r: 6 }}
            type="linear"
          >
            <LabelList dataKey="blue" content={BlueLabel} />
          </Line>
          <ChartLegend content={<ChartLegendContent />} />
        </LineChart>
      </ChartContainer>
    </div>
  );
}
