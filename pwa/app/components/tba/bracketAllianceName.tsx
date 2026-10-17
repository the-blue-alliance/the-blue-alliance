import { cn } from 'cn';
import { type JSX } from 'react';

const HIGHLIGHT_COLORS = {
  red: 'bg-red-100 dark:bg-red-900',
  blue: 'bg-blue-100 dark:bg-blue-900',
};

interface BracketAllianceNameProps {
  name: string;
  color: keyof typeof HIGHLIGHT_COLORS;
  isHighlighted: boolean;
}

export default function BracketAllianceName({
  name,
  color,
  isHighlighted,
}: BracketAllianceNameProps): JSX.Element {
  return (
    <span
      data-name={name}
      className="inline-grid items-baseline justify-items-center after:invisible
        after:col-start-1 after:row-start-1 after:text-sm
        after:content-[attr(data-name)]"
    >
      <span
        className={cn(
          'col-start-1 row-start-1 transition-colors duration-200',
          isHighlighted && [
            '-mx-1 rounded px-1 text-sm dark:text-white',
            HIGHLIGHT_COLORS[color],
          ],
        )}
      >
        {name}
      </span>
    </span>
  );
}
