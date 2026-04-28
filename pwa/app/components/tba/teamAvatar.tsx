import { useState } from 'react';

import { MediaAvatar } from '~/api/tba/read';
import { cn } from '~/lib/utils';

export default function TeamAvatar({
  media,
  className,
  defaultRed = false,
}: {
  media: MediaAvatar;
  className?: string;
  defaultRed?: boolean;
}) {
  const [colorClass, setColorClass] = useState(
    defaultRed ? 'bg-first-avatar-red' : 'bg-first-avatar-blue',
  );

  if (!media.details) {
    return null;
  }

  const handler = () => {
    if (colorClass === 'bg-first-avatar-blue') {
      setColorClass('bg-first-avatar-red');
    } else {
      setColorClass('bg-first-avatar-blue');
    }
  };

  return (
    <button onClick={handler} onKeyDown={handler} className={className}>
      <img
        alt="Team Avatar"
        src={`data:image/png;base64, ${media.details.base64Image}`}
        className={cn('inline size-12 rounded p-1', colorClass)}
      />
    </button>
  );
}
