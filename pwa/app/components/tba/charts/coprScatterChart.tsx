import { useEffect, useState } from 'react';
import {
  Cell,
  Label,
  LabelList,
  ReferenceLine,
  Scatter,
  ScatterChart,
  Tooltip,
  TooltipProps,
  XAxis,
  YAxis,
} from 'recharts';
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent';

import { EventColors, TeamWithColor } from '~/api/colors';
import type { EventCopRs } from '~/api/v3';
import { Card, CardContent, CardHeader, CardTitle } from '~/components/ui/card';
import { ChartContainer } from '~/components/ui/chart';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
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

function generateDomain(dataMin: number, dataMax: number): [number, number] {
  if (dataMax > 1) {
    return [dataMin > 0 ? 0 : Math.floor(dataMin - 1), Math.ceil(dataMax + 1)];
  }

  return [-0.1, 1];
}

// If a team has a white primary color, it doesn't show up on the chart
function getNonWhiteTeamColor(
  colors: EventColors,
  teamKey: string,
): TeamWithColor {
  const color = colors.teams[teamKey.substring(3)] ?? {
    teamNumber: 0,
    colors: {
      verified: false,
      primaryHex: 'hsl(var(--primary))',
      secondaryHex: 'hsl(var(--primary))',
    },
  };

  if (color.colors?.primaryHex === '#ffffff') {
    color.colors.primaryHex = '#000000';
  }

  return color;
}

export default function CoprScatterChart({
  coprs,
  colors,
}: {
  coprs: EventCopRs;
  colors: EventColors;
}) {
  const [selectedXCopr, setSelectedXCopr] = useState('teleopPoints');
  const [selectedYCopr, setSelectedYCopr] = useState('autoPoints');
  const [data, setData] = useState<Datapoint[]>([]);

  useEffect(() => {
    const data: Datapoint[] = Object.keys(coprs[selectedXCopr])
      .map((tk) => ({
        teamKey: tk,
        valueX: coprs[selectedXCopr][tk],
        valueY: coprs[selectedYCopr][tk],
      }))
      .sort((a, b) => a.valueX - b.valueX);

    setData(data);
  }, [selectedXCopr, selectedYCopr, coprs]);

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between">
          <div>
            <CardTitle>Component OPRs</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pb-1">
        <ChartContainer
          config={{
            teamKey: { color: 'hsl(var(--primary))' },
            valueX: { label: selectedXCopr, color: 'hsl(var(--primary))' },
            valueY: { label: selectedYCopr, color: 'hsl(var(--primary))' },
            label: {
              color: 'hsl(var(--primary))',
            },
          }}
        >
          <ScatterChart
            data={data}
            margin={{
              left: 0,
              right: 0,
              bottom: 10,
              top: 10,
            }}
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
              <Label value={camelCaseToHumanReadable(selectedXCopr)} dy={17} />
            </XAxis>
            <YAxis
              dataKey="valueY"
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
                dx={-20}
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
            <Scatter>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={
                    getNonWhiteTeamColor(colors, entry.teamKey).colors
                      ?.primaryHex
                  }
                />
              ))}

              <LabelList
                dataKey={'teamKey'}
                position={'top'}
                formatter={(value: string) => value.substring(3)}
              />
            </Scatter>
          </ScatterChart>
        </ChartContainer>
      </CardContent>
      <div className="flex flex-row justify-around pb-4">
        <div className="flex flex-row items-center">
          <div className="pr-4 font-bold">Y Axis</div>
          <Select value={selectedYCopr} onValueChange={setSelectedYCopr}>
            <SelectTrigger className="w-auto">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>Y Axis</SelectLabel>
                {Object.keys(coprs).map((k) => (
                  <SelectItem value={k} key={k}>
                    {camelCaseToHumanReadable(k)}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-row items-center">
          <div className="pr-4 font-bold">X Axis</div>
          <Select value={selectedXCopr} onValueChange={setSelectedXCopr}>
            <SelectTrigger className="w-auto">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>X Axis</SelectLabel>
                {Object.keys(coprs).map((k) => (
                  <SelectItem value={k} key={k}>
                    {camelCaseToHumanReadable(k)}
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
}: TooltipProps<ValueType, NameType> & { xCopr: string; yCopr: string }) => {
  if (active && payload && payload.length > 1) {
    const teamKey = (
      payload[0].payload as { teamKey: string }
    ).teamKey.substring(3);

    return (
      <div className="flex flex-col rounded-md bg-white shadow-xl">
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
