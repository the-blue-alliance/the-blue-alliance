import { type ComponentType, type ReactNode, useState } from 'react';

import BiChevronBarDown from '~icons/bi/chevron-bar-down';
import BiChevronBarUp from '~icons/bi/chevron-bar-up';

import { Button } from '~/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '~/components/ui/card';

/**
 * Shared card chrome for insight components (leaderboards, streaks, etc.):
 * an icon, title/subtitle, and an expand/collapse toggle over a scrollable
 * body. `children` is a render prop so callers can size their table body to
 * the shared `expanded` state.
 */
export function InsightCard({
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  icon: ComponentType<{ className?: string }>;
  title: ReactNode;
  subtitle?: ReactNode;
  children: (expanded: boolean) => ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card
      className="overflow-hidden border-border/50 shadow-sm transition-shadow
        hover:shadow-md"
    >
      <CardHeader
        className="border-b bg-gradient-to-br from-muted/30 to-muted/10 px-6
          pt-5 pb-4"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg
                bg-primary/10"
            >
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-lg leading-tight font-semibold">
                {title}
              </CardTitle>
              {subtitle && (
                <CardDescription className="mt-0.5 text-sm">
                  {subtitle}
                </CardDescription>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            onClick={() => {
              setExpanded(!expanded);
            }}
            size="sm"
            className="h-9 w-9 p-0 hover:bg-primary/10"
          >
            {expanded ? (
              <BiChevronBarUp className="h-4 w-4" />
            ) : (
              <BiChevronBarDown className="h-4 w-4" />
            )}
            <span className="sr-only">Toggle</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">{children(expanded)}</CardContent>
    </Card>
  );
}
