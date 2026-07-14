import MaterialSymbolsLocalFireDepartment from '~icons/material-symbols/local-fire-department';

import { type InsightV2Streak } from '~/api/tba/read';
import { InsightCard } from '~/components/tba/insightCard';
import { EventLink, TeamLink } from '~/components/tba/links';
import { Badge } from '~/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import {
  PRE_EXPANDED_ROWS,
  rankRowClassName,
  rankTextClassName,
} from '~/lib/insightUtils';
import { cn } from '~/lib/utils';

export function StreakInsight({
  streak,
  subtitle,
}: {
  streak: InsightV2Streak;
  subtitle?: string;
}) {
  return (
    <InsightCard
      icon={MaterialSymbolsLocalFireDepartment}
      title={streak.display_name}
      subtitle={subtitle}
    >
      {(expanded) => (
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead className="h-10 w-[4.5rem] text-center font-semibold">
                Length
              </TableHead>
              <TableHead className="h-10 text-left font-semibold">
                Team
              </TableHead>
              <TableHead className="h-10 text-left font-semibold">
                Range
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {streak.data.entries
              .slice(0, expanded ? 100 : PRE_EXPANDED_ROWS)
              .map((entry, i) => {
                const rank = i + 1;

                return (
                  <TableRow
                    key={`${entry.key}-${entry.start}`}
                    className={cn(
                      'transition-colors hover:bg-muted/50',
                      rankRowClassName(rank),
                    )}
                  >
                    <TableCell
                      className={cn(
                        'text-center font-semibold numeric-data',
                        rank <= 3 && 'text-base',
                        rankTextClassName(rank),
                      )}
                    >
                      {entry.streak_length}
                    </TableCell>
                    <TableCell className="py-3 pl-4 text-left">
                      <StreakKeyLink
                        keyType={entry.key_type}
                        keyVal={entry.key}
                      />
                    </TableCell>
                    <TableCell className="py-3 pl-4 text-left">
                      <StreakRangeLabel start={entry.start} end={entry.end} />
                      {entry.is_active && (
                        <Badge variant="success" className="ml-2 align-middle">
                          Active
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>
      )}
    </InsightCard>
  );
}

function StreakKeyLink({
  keyType,
  keyVal,
}: {
  keyType: InsightV2Streak['data']['entries'][number]['key_type'];
  keyVal: string;
}) {
  if (keyType === 'team') {
    return (
      <TeamLink teamOrKey={keyVal} year={0}>
        {keyVal.substring(3)}
      </TeamLink>
    );
  }
  if (keyType === 'event') {
    return <EventLink eventOrKey={keyVal}>{keyVal}</EventLink>;
  }
  return <>{keyVal}</>;
}

/**
 * Streak `start`/`end` values are either event keys (e.g. `2024casj`) or bare
 * year strings (e.g. `2024`), depending on the granularity of the streak.
 */
function StreakRangeLabel({ start, end }: { start: string; end: string }) {
  const startIsEvent = /^\d{4}[a-z0-9]+$/.test(start);
  const endIsEvent = /^\d{4}[a-z0-9]+$/.test(end);

  return (
    <>
      {startIsEvent ? <EventLink eventOrKey={start}>{start}</EventLink> : start}
      {' – '}
      {end === start ? (
        <span className="text-muted-foreground">(same)</span>
      ) : endIsEvent ? (
        <EventLink eventOrKey={end}>{end}</EventLink>
      ) : (
        end
      )}
    </>
  );
}
