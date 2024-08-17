import { useEffect, useState } from 'react';
import {
  CartesianGrid,
  Cell,
  Label,
  LabelList,
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

import { EventColors } from '~/api/colors';
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

interface Datapoint {
  teamKey: string;
  valueX: number;
  valueY: number;
}

export default function CoprScatterChart({
  coprs,
  colors,
}: {
  coprs: EventCopRs;
  colors: EventColors;
}) {
  const [selectedXCopr, setSelectedXCopr] = useState(
    'Total Teleop Game Pieces',
  );
  const [selectedYCopr, setSelectedYCopr] = useState('Total Auto Game Pieces');
  const [data, setData] = useState<Datapoint[]>([
    { teamKey: '604', valueX: 2, valueY: 3 },
    { teamKey: '2713', valueX: 4, valueY: 5 },
  ]);

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
          <Select value={selectedXCopr} onValueChange={setSelectedXCopr}>
            <SelectTrigger className="w-auto">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>COPRs</SelectLabel>
                {Object.keys(coprs).map((k) => (
                  <SelectItem value={k} key={k}>
                    {k}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
          <Select value={selectedYCopr} onValueChange={setSelectedYCopr}>
            <SelectTrigger className="w-auto">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectLabel>COPRs</SelectLabel>
                {Object.keys(coprs).map((k) => (
                  <SelectItem value={k} key={k}>
                    {k}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
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
              bottom: 20,
              top: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="valueX"
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              type="number"
            >
              <Label value={selectedXCopr} dy={17} />
            </XAxis>
            <YAxis dataKey="valueY" axisLine={false} tickLine={false}>
              <Label value={selectedYCopr} angle={-90} dx={-20} />
            </YAxis>
            <Tooltip
              content={
                <CustomTooltip xCopr={selectedXCopr} yCopr={selectedYCopr} />
              }
            />
            <Scatter>
              {data.map((entry, index) => {
                const color = colors.teams[entry.teamKey.substring(3)] ?? {
                  teamNumber: 0,
                  colors: {
                    verified: false,
                    primaryHex: 'hsl(var(--primary))',
                    secondaryHex: 'hsl(var(--primary))',
                  },
                };

                return (
                  <Cell key={`cell-${index}`} fill={color.colors?.primaryHex} />
                );
              })}

              <LabelList
                dataKey={'teamKey'}
                position={'top'}
                formatter={(value: string) => value.substring(3)}
              />
            </Scatter>
          </ScatterChart>
        </ChartContainer>
      </CardContent>
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
    // Justin: I don't know how to fix the typing on this but IN THIS COMPONENT it should be fine
    // todo: fix this horrible nonsense
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access
    const teamKey = payload[0].payload.teamKey.substring(3);

    return (
      <div className="custom-tooltip">
        <Card className="max-w-[40vw]">
          <CardHeader>
            <CardTitle className="text-base">{teamKey}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between gap-4">
              <div>{xCopr}</div>
              <div>{Number(payload[0].value).toFixed(2)}</div>
            </div>
            <div className="flex justify-between gap-4">
              <div>{yCopr}</div>
              <div>{Number(payload[1].value).toFixed(2)}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};
