import type { Webcast } from '~/api/tba/read';

/**
 * Renders the appropriate embed for a webcast based on its type.
 */
export function WebcastEmbed({ webcast }: { webcast: Webcast }) {
  switch (webcast.type) {
    case 'youtube':
      return <YouTubeEmbed channel={webcast.channel} />;
    case 'twitch':
      return <TwitchEmbed channel={webcast.channel} />;
    default:
      return <UnsupportedEmbed type={webcast.type} />;
  }
}

function YouTubeEmbed({ channel }: { channel: string }) {
  const src = `https://www.youtube.com/embed/${channel}?autoplay=1&mute=1`;
  return (
    <iframe
      className="h-full w-full"
      src={src}
      title="YouTube video player"
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
      allowFullScreen
    />
  );
}

function TwitchEmbed({ channel }: { channel: string }) {
  // Need to use the current hostname for Twitch's parent parameter
  const hostname =
    typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const src = `https://player.twitch.tv/?channel=${channel}&parent=${hostname}&muted=true`;
  return (
    <iframe
      className="h-full w-full"
      src={src}
      title="Twitch stream"
      allowFullScreen
    />
  );
}

function UnsupportedEmbed({ type }: { type: string }) {
  return (
    <div
      className="flex h-full w-full flex-col items-center justify-center
        bg-slate-800 text-white"
    >
      <p className="text-lg">
        Webcast type &quot;{type}&quot; is not supported
      </p>
      <p className="mt-2 text-sm text-slate-400">
        Only YouTube and Twitch webcasts are supported
      </p>
    </div>
  );
}
