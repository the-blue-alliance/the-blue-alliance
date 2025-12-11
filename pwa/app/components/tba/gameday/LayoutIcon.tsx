import { getLayoutById } from '~/lib/gameday/layouts';
import { cn } from '~/lib/utils';

export function LayoutIcon({
  layoutId,
  className,
  color = 'currentColor',
}: {
  layoutId: number;
  className?: string;
  color?: string;
}) {
  const layout = getLayoutById(layoutId);
  if (!layout) return null;

  return (
    <svg
      viewBox="0 0 23 15"
      className={cn('inline-block', className)}
      fill={color}
    >
      <path d={layout.svgPath} />
    </svg>
  );
}
