import { Link } from '@tanstack/react-router';

import CheckIcon from '~icons/lucide/check';
import ChevronDownIcon from '~icons/lucide/chevron-down';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import { cn } from '~/lib/utils';

export interface YearSelectorOption {
  label: string;
  to: string;
  isCurrent?: boolean;
}

interface YearSelectorProps {
  options: YearSelectorOption[];
  currentLabel: string;
  triggerClassName?: string;
  contentClassName?: string;
}

export function YearSelector({
  options,
  currentLabel,
  triggerClassName,
  contentClassName,
}: YearSelectorProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        className={cn(
          `flex h-10 w-full cursor-pointer items-center justify-between
          rounded-md border border-input bg-background px-3 py-2 text-sm
          ring-offset-background focus:ring-2 focus:ring-ring
          focus:ring-offset-2 focus:outline-hidden disabled:cursor-not-allowed
          disabled:opacity-50`,
          triggerClassName,
        )}
      >
        <span className="line-clamp-1">{currentLabel}</span>
        <ChevronDownIcon className="ml-2 size-4 shrink-0 opacity-50" />
      </DropdownMenuTrigger>
      <DropdownMenuContent
        className={cn(
          'max-h-[30vh] w-(--radix-dropdown-menu-trigger-width) overflow-y-auto',
          contentClassName,
        )}
      >
        {options.map((option) => (
          <DropdownMenuItem key={option.to} asChild>
            <Link
              to={option.to}
              className="flex cursor-pointer items-center gap-2 text-foreground
                no-underline"
            >
              <CheckIcon
                className={cn(
                  'size-4 shrink-0',
                  !option.isCurrent && 'invisible',
                )}
              />
              {option.label}
            </Link>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
