import { cn } from 'cn';
import { useEffect, useState } from 'react';

interface YoutubeEmbedProps {
  videoId: string;
  title: string;
  className?: string;
  deferUntilIdle?: boolean;
}

export function YoutubeEmbed({
  videoId,
  title,
  className,
  deferUntilIdle = false,
}: YoutubeEmbedProps) {
  const [shouldLoad, setShouldLoad] = useState(!deferUntilIdle);

  useEffect(() => {
    if (!deferUntilIdle) {
      return;
    }

    let idleCallbackId: number | undefined;
    let fallbackTimeoutId: number | undefined;

    const scheduleLoad = () => {
      const requestIdleCallback = window.requestIdleCallback as
        typeof window.requestIdleCallback | undefined;
      if (requestIdleCallback) {
        idleCallbackId = requestIdleCallback(() => setShouldLoad(true), {
          timeout: 2_000,
        });
      } else {
        fallbackTimeoutId = window.setTimeout(() => setShouldLoad(true), 1_000);
      }
    };

    if (document.readyState === 'complete') {
      scheduleLoad();
    } else {
      window.addEventListener('load', scheduleLoad, { once: true });
    }

    return () => {
      window.removeEventListener('load', scheduleLoad);
      if (idleCallbackId !== undefined) {
        window.cancelIdleCallback(idleCallbackId);
      }
      if (fallbackTimeoutId !== undefined) {
        window.clearTimeout(fallbackTimeoutId);
      }
    };
  }, [deferUntilIdle]);

  return (
    <div className={cn('relative aspect-video h-auto w-full', className)}>
      {shouldLoad ? (
        <iframe
          src={`https://www.youtube.com/embed/${videoId.replace('?t=', '?start=')}`}
          title={title}
          allowFullScreen
          loading="lazy"
          className="absolute inset-0 h-full w-full rounded-lg shadow-lg"
        />
      ) : (
        <div
          data-testid="youtube-embed-placeholder"
          className="absolute inset-0 h-full w-full animate-pulse rounded-lg
            bg-muted shadow-lg"
        >
          <span className="sr-only">Loading {title}</span>
        </div>
      )}
    </div>
  );
}
