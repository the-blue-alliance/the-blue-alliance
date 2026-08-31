import { useMemo, useState } from 'react';

import MaterialSymbolsTarget from '~icons/material-symbols/target';

import {
  type InsightV2SuccessRate,
  type InsightV2SuccessRateEntry,
} from '~/api/tba/read';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '~/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { Tabs, TabsList, TabsTrigger } from '~/components/ui/tabs';
import {
  type MatchLevel,
  formatSuccessRate,
  otherMatchLevel,
} from '~/lib/successRateUtils';
import { cn } from '~/lib/utils';

export function SuccessRateInsight({
  insight,
  subtitle,
}: {
  insight: InsightV2SuccessRate;
  subtitle?: string;
}) {
  // The payload also carries a scope per event; this card covers the season
  // and its weeks only.
  const scopes = useMemo(
    () => insight.data.scopes.filter((s) => s.scope_type !== 'event'),
    [insight.data.scopes],
  );
  const scopeItems = useMemo(
    () => scopes.map((s, i) => ({ value: String(i), label: s.label })),
    [scopes],
  );

  const [scopeIndex, setScopeIndex] = useState(0);
  const [matchLevel, setMatchLevel] = useState<MatchLevel>('qual');

  const scope = scopes[scopeIndex] ?? scopes[0];
  if (scope === undefined) {
    return null;
  }

  const rates = scope[matchLevel];
  const fallbackLevel = otherMatchLevel(matchLevel);

  return (
    <Card className="overflow-hidden border-border/50 shadow-sm">
      <CardHeader
        className="border-b bg-linear-to-br from-muted/30 to-muted/10 px-6 pt-5
          pb-4"
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg
                bg-primary/10"
            >
              <MaterialSymbolsTarget className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg leading-tight font-semibold">
                {insight.display_name}
              </CardTitle>
              {subtitle && (
                <CardDescription className="mt-0.5 text-sm">
                  {subtitle}
                </CardDescription>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Select
              items={scopeItems}
              value={String(scopeIndex)}
              onValueChange={(value) => {
                if (value !== null) {
                  setScopeIndex(Number(value));
                }
              }}
            >
              <SelectTrigger className="w-[11rem]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {scopeItems.map(({ value, label }) => (
                  <SelectItem value={value} key={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Tabs
              value={matchLevel}
              onValueChange={(value) => {
                setMatchLevel(value as MatchLevel);
              }}
            >
              <TabsList>
                <TabsTrigger value="qual">Quals</TabsTrigger>
                <TabsTrigger value="playoff">Playoffs</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {rates.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">
            No {matchLevel === 'qual' ? 'qualification' : 'playoff'} match data
            for {scope.label}.
            {scope[fallbackLevel].length > 0 &&
              ` Try the ${fallbackLevel === 'qual' ? 'Quals' : 'Playoffs'} tab.`}
          </p>
        ) : (
          <SuccessRateTable rates={rates} />
        )}
      </CardContent>
    </Card>
  );
}

export function SuccessRateTable({
  rates,
}: {
  rates: InsightV2SuccessRateEntry[];
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead className="h-10 pl-4 text-left font-semibold">
            Statistic
          </TableHead>
          <TableHead className="h-10 w-24 text-right font-semibold">
            Count
          </TableHead>
          <TableHead className="h-10 w-32 text-right font-semibold">
            Opportunities
          </TableHead>
          <TableHead className="h-10 w-28 pr-4 text-right font-semibold">
            % Success
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rates.map((rate) => (
          <TableRow
            key={rate.name}
            className="transition-colors hover:bg-muted/50"
          >
            <TableCell className="py-3 pl-4 text-left font-medium">
              {rate.label}
            </TableCell>
            <TableCell className="text-right numeric-data">
              {rate.count.toLocaleString()}
            </TableCell>
            <TableCell className="text-right numeric-data">
              {rate.opportunities.toLocaleString()}
            </TableCell>
            <TableCell
              className={cn(
                'pr-4 text-right font-semibold numeric-data',
                rate.opportunities === 0 && 'text-muted-foreground',
              )}
            >
              {formatSuccessRate(rate)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
