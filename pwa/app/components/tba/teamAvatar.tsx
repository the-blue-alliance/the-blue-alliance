import { useState } from 'react';
import { Media } from '~/api/v3';
import { cn } from '~/lib/utils';

export default function TeamAvatar({ media }: { media: Media }): JSX.Element {
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
    <img
      alt="Team Avatar"
      src={`data:image/png;base64, ${media.details.base64Image}`}
      className={cn(
        'size-12 rounded inline mr-2 p-1 cursor-pointer',
        colorClass,
      )}
      onClick={handler}
      onKeyDown={handler}
    />
  );
}
