import { cn } from '~/lib/utils';

export function YoutubeEmbed({
  videoId,
  title,
  className,
}: {
  videoId: string;
  title: string;
  className?: string;
}) {
  return (
    <div className={cn('relative aspect-video h-auto w-full', className)}>
      <iframe
        src={`https://www.youtube.com/embed/${videoId}`}
        title={title}
        allowFullScreen
        className="absolute inset-0 h-full w-full rounded-lg shadow-lg"
      />
    </div>
  );
}
