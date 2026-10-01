import { useRouterState } from '@tanstack/react-router';
import { useEffect, useState } from 'react';

import { Progress } from '~/components/ui/progress';

// TODO: Integrate with nav bar
export default function GlobalLoadingProgress() {
  const active = useRouterState({ select: (s) => s.isLoading });

  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<'idle' | 'loading' | 'done'>('idle');
  const [prevActive, setPrevActive] = useState(active);

  if (active !== prevActive) {
    setPrevActive(active);
    if (active) {
      // Start at 15% to give the impression of a fast start
      setProgress(15);
      setPhase('loading');
    } else {
      setProgress(100);
      setPhase('done');
    }
  }

  useEffect(() => {
    if (phase !== 'loading') {
      return;
    }
    const interval = setInterval(() => {
      // Advance 30% of the remaining progress, stalling at 95% until the navigation is complete
      setProgress((prevProgress) => {
        const remaining = 95 - prevProgress;
        return Math.min(95, prevProgress + 0.3 * remaining);
      });
    }, 200);
    return () => {
      clearInterval(interval);
    };
  }, [phase]);

  useEffect(() => {
    if (phase !== 'done') {
      return;
    }
    // Wait before hiding the progress bar so the user sees it at 100%
    const timeout = setTimeout(() => {
      setPhase('idle');
    }, 250);
    return () => {
      clearTimeout(timeout);
    };
  }, [phase]);

  if (phase === 'idle') {
    return null;
  }
  return (
    <Progress
      className="fixed top-0 z-100 h-0.5 rounded-none
        [&_[data-slot=progress-indicator]]:dark:bg-secondary-foreground"
      value={progress}
    />
  );
}
