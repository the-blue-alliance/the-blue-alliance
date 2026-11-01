import { Skeleton } from '~/components/ui/skeleton';

/**
 * Placeholder for a page whose data is still loading in the browser. Every
 * repeat visit shows it, since the app shell has no route data. It fills the
 * screen so the footer starts below it and does not jump when the page
 * renders.
 */
export default function PageLoadingSkeleton() {
  return (
    <output aria-label="Loading page" className="block space-y-4">
      <Skeleton className="h-9 w-3/4 max-w-lg" />
      <Skeleton className="h-5 w-1/2 max-w-xs" />
      <Skeleton className="h-svh w-full" />
    </output>
  );
}
