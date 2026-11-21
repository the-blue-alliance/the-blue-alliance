import { cn } from 'cn';
import { useEffect, useState } from 'react';

import PlayIcon from '~icons/lucide/play';

interface YoutubeEmbedProps {
  videoId: string;
  title: string;
  className?: string;
  deferUntilIdle?: boolean;
  /** Show a thumbnail and load the player only when clicked. */
  clickToPlay?: boolean;
}

export function YoutubeEmbed({
  videoId,
  title,
  className,
  deferUntilIdle = false,
  clickToPlay = false,
}: YoutubeEmbedProps) {
  const [shouldLoad, setShouldLoad] = useState(!deferUntilIdle);
  const [playing, setPlaying] = useState(false);

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

  if (clickToPlay) {
    const src = `https://www.youtube.com/embed/${videoId.replace('?t=', '?start=')}`;
    return (
      <div className={cn('relative aspect-video h-auto w-full', className)}>
        {playing ? (
          <iframe
            src={`${src}${src.includes('?') ? '&' : '?'}autoplay=1`}
            title={title}
            allow="autoplay; encrypted-media; picture-in-picture"
            allowFullScreen
            className="absolute inset-0 h-full w-full rounded-lg shadow-lg"
          />
        ) : (
          <PlayButton title={title} onClick={() => setPlaying(true)}>
            <img
              src={`https://i.ytimg.com/vi/${videoId.split('?')[0]}/mqdefault.jpg`}
              alt=""
              loading="lazy"
              className="absolute inset-0 h-full w-full object-cover"
            />
          </PlayButton>
        )}
      </div>
    );
  }

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

interface TwitchEmbedProps {
  channel: string;
  title: string;
  className?: string;
}

/** A Twitch channel player that loads only when clicked. */
export function TwitchEmbed({ channel, title, className }: TwitchEmbedProps) {
  const [playing, setPlaying] = useState(false);
  return (
    <div className={cn('relative aspect-video h-auto w-full', className)}>
      {playing ? (
        <iframe
          // Twitch refuses to play unless parent names the embedding host
          src={`https://player.twitch.tv/?channel=${encodeURIComponent(channel)}&parent=${window.location.hostname}`}
          title={title}
          allow="autoplay; fullscreen"
          allowFullScreen
          className="absolute inset-0 h-full w-full rounded-lg shadow-lg"
        />
      ) : (
        <PlayButton title={title} onClick={() => setPlaying(true)}>
          <span
            className="absolute inset-x-0 bottom-0 truncate px-3 py-2 text-left
              text-sm font-medium"
          >
            twitch.tv/{channel}
          </span>
        </PlayButton>
      )}
    </div>
  );
}

function PlayButton({
  title,
  onClick,
  children,
}: {
  title: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={`Play ${title}`}
      onClick={onClick}
      className="group absolute inset-0 overflow-hidden rounded-lg bg-muted
        shadow-lg"
    >
      {children}
      <span
        className="absolute top-1/2 left-1/2 flex size-12 -translate-1/2
          items-center justify-center rounded-full bg-black/70 text-white
          transition-colors group-hover:bg-red-600"
      >
        <PlayIcon className="size-6 translate-x-px" />
      </span>
    </button>
  );
}
