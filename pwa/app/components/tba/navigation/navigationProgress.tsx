import { useRouterState } from '@tanstack/react-router';

export function NavigationProgress(): React.JSX.Element | null {
  const isLoading = useRouterState({ select: (s) => s.isLoading });

  if (!isLoading) {
    return null;
  }

  return (
    <div
      role="progressbar"
      aria-label="Loading page"
      className="fixed inset-x-0 inset-bs-0 z-60 h-0.75 overflow-clip
        transition-opacity delay-150 duration-200 starting:opacity-0"
    >
      <div
        className="h-full w-full bg-white/85 motion-safe:w-2/5
          motion-safe:animate-navigation-progress"
      />
    </div>
  );
}
