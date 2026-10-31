import { cn } from 'cn';

import { Skeleton } from '~/components/ui/skeleton';

export default function LoadingSkeleton({
  label,
  className,
}: {
  label: string;
  className?: string;
}) {
  return (
    <output aria-label={label} className={cn('block', className)}>
      <Skeleton className="size-full rounded-[inherit]" />
    </output>
  );
}
