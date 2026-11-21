import type { ReactNode } from 'react';

import { Media } from '~/api/tba/read';
import { MediaIcon } from '~/components/tba/socialBadges';

export default function TeamSocialMediaList({
  socials,
  children,
}: {
  socials: Media[];
  children?: ReactNode;
}) {
  return (
    <div
      className="my-2 flex flex-wrap justify-center gap-1 md:my-0
        md:justify-start"
    >
      {socials
        .toSorted((a, b) => a.type.localeCompare(b.type))
        .map((m) => (
          <MediaIcon media={m} key={`${m.type}-${m.foreign_key}`} />
        ))}
      {children}
    </div>
  );
}
