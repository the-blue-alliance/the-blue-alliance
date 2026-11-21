import { cn } from 'cn';
import { useState } from 'react';

import { MediaAvatar } from '~/api/tba/read';
import defaultAvatar from '~/images/default-avatar.png';

const RED_ACCENT = 'bg-alliance-red-accent';
const BLUE_ACCENT = 'bg-alliance-blue-accent';

export default function TeamAvatar({
  media,
  className,
  defaultRed = false,
}: {
  media: MediaAvatar | undefined;
  className?: string;
  defaultRed?: boolean;
}) {
  const [colorClass, setColorClass] = useState(
    defaultRed ? RED_ACCENT : BLUE_ACCENT,
  );

  const handler = () => {
    if (colorClass === BLUE_ACCENT) {
      setColorClass(RED_ACCENT);
    } else {
      setColorClass(BLUE_ACCENT);
    }
  };

  return (
    <button onClick={handler} onKeyDown={handler} className={className}>
      <img
        alt={media?.details ? 'Team Avatar' : 'Default Team Avatar'}
        src={
          media?.details
            ? `data:image/png;base64, ${media.details.base64Image}`
            : defaultAvatar
        }
        className={cn('inline size-12 rounded p-1', colorClass)}
      />
    </button>
  );
}
