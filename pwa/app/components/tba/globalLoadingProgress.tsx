import { useNavigation } from '@remix-run/react';
import { useEffect, useState } from 'react';

import { Progress } from '~/components/ui/progress';

// TODO: Integrate with nav bar
export default function GlobalLoadingProgress() {
  const [hidden, setHidden] = useState(true);
  const [progress, setProgress] = useState(0);
  const navigation = useNavigation();
  const active = navigation.state !== 'idle';

  useEffect(() => {
    if (active) {
      // Start at 15% to give the impression of a fast start
      setProgress(15);
      setHidden(false);
    } else {
      // Wait before hiding the progress bar so the user sees it at 100%
      setProgress(100);
      const timeout = setTimeout(() => {
        setHidden(true);
      }, 250);
      return () => {
        clearTimeout(timeout);
      };
    }
  }, [active]);

  useEffect(() => {
    if (!active || hidden) {
      return;
    }
    const interval = setInterval(() => {
      // Advance 30% of the remaining progress, stalling at 95% until the navigation is complete
      setProgress((prevProgres) => {
        const remaining = 95 - prevProgres;
        return Math.min(95, prevProgres + 0.3 * remaining);
      });
    }, 200);
    return () => {
      clearInterval(interval);
    };
  }, [active, hidden]);

  if (hidden) {
    return null;
  }
  return (
    <Progress
      className="fixed top-0 z-20 h-0.5 rounded-none"
      value={progress}
    />
  );
}
