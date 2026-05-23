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
    defaultRed ? 'bg-alliance-red-bg' : 'bg-alliance-blue-bg',
  );

  if (!media.details) {
    return null;
  }

  const handler = () => {
    if (colorClass === 'bg-alliance-blue-bg') {
      setColorClass('bg-alliance-red-bg');
    } else {
      setColorClass('bg-alliance-blue-bg');
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
