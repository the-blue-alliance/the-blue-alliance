import { cn } from '~/lib/utils';

interface DetailEntityProps {
  icon: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}

export default function DetailEntity({
  icon,
  className,
  children,
}: DetailEntityProps) {
  return (
    <div className={cn('flex items-center gap-2 [&>svg]:size-4', className)}>
      {icon}
      <span>{children}</span>
    </div>
  );
}
