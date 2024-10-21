import { useState } from 'react';

import { Media } from '~/api/v3';
import { cn } from '~/lib/utils';

export default function TeamAvatar({
  media,
}: {
  media: Media;
}): React.JSX.Element {
  const [colorClass, setColorClass] = useState('bg-first-avatar-blue');

  if (!media.details) {
    return <></>;
  }

  const handler = () => {
    if (colorClass === 'bg-first-avatar-blue') {
      setColorClass('bg-first-avatar-red');
    } else {
      setColorClass('bg-first-avatar-blue');
    }
  };

  return (
    <button className="mr-3" onClick={handler} onKeyDown={handler}>
      <img
        alt="Team Avatar"
        src={`data:image/png;base64, ${media.details.base64Image}`}
        className={cn('size-12 rounded inline p-1', colorClass)}
      />
    </button>
  );
}
