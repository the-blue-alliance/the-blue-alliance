import { Media } from '~/api/tba/read';
import { MediaIcon } from '~/components/tba/socialBadges';

export default function TeamSocialMediaList({ socials }: { socials: Media[] }) {
  socials.sort((a, b) => a.type.localeCompare(b.type));

  return (
    <div
      className="my-2 flex flex-wrap justify-center gap-1 md:my-0
        md:justify-start"
    >
      {socials.map((m) => (
        <MediaIcon media={m} key={`${m.type}-${m.foreign_key}`} />
      ))}
    </div>
  );
}
