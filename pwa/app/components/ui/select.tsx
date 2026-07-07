import { Select as SelectPrimitive } from '@base-ui/react/select';
import { type ComponentProps } from 'react';

import CheckIcon from '~icons/lucide/check';
import ChevronDownIcon from '~icons/lucide/chevron-down';
import ChevronUpIcon from '~icons/lucide/chevron-up';

import { cn } from '~/lib/utils';

const Select = SelectPrimitive.Root;

const SelectGroup = SelectPrimitive.Group;

const SelectValue = SelectPrimitive.Value;

function SelectTrigger({
  className,
  children,
  ...props
}: ComponentProps<typeof SelectPrimitive.Trigger>) {
  return (
    <SelectPrimitive.Trigger
      className={cn(
        `flex h-10 w-full cursor-pointer items-center justify-between rounded-md
        border border-input bg-background px-3 py-2 text-sm
        ring-offset-background placeholder:text-muted-foreground focus:ring-2
        focus:ring-ring focus:ring-offset-2 focus:outline-hidden
        disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1`,
        className,
      )}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon
        render={<ChevronDownIcon className="size-4 opacity-50" />}
      />
    </SelectPrimitive.Trigger>
  );
}

function SelectScrollUpButton({
  className,
  ...props
}: ComponentProps<typeof SelectPrimitive.ScrollUpArrow>) {
  return (
    <SelectPrimitive.ScrollUpArrow
      className={cn(
        'flex cursor-pointer items-center justify-center py-1',
        className,
      )}
      {...props}
    >
      <ChevronUpIcon className="size-4" />
    </SelectPrimitive.ScrollUpArrow>
  );
}

function SelectScrollDownButton({
  className,
  ...props
}: ComponentProps<typeof SelectPrimitive.ScrollDownArrow>) {
  return (
    <SelectPrimitive.ScrollDownArrow
      className={cn(
        'flex cursor-pointer items-center justify-center py-1',
        className,
      )}
      {...props}
    >
      <ChevronDownIcon className="size-4" />
    </SelectPrimitive.ScrollDownArrow>
  );
}

function SelectContent({
  className,
  children,
  side,
  sideOffset,
  align,
  alignOffset,
  alignItemWithTrigger = false,
  ...props
}: ComponentProps<typeof SelectPrimitive.Popup> &
  Pick<
    ComponentProps<typeof SelectPrimitive.Positioner>,
    'side' | 'sideOffset' | 'align' | 'alignOffset' | 'alignItemWithTrigger'
  >) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Positioner
        side={side}
        sideOffset={sideOffset}
        align={align}
        alignOffset={alignOffset}
        alignItemWithTrigger={alignItemWithTrigger}
        className="isolate z-50"
      >
        <SelectPrimitive.Popup
          className={cn(
            `relative z-50 max-h-(--available-height) min-w-[8rem]
            overflow-x-hidden overflow-y-auto rounded-md border bg-popover
            text-popover-foreground shadow-md data-[side=bottom]:translate-y-1
            data-[side=bottom]:slide-in-from-top-2
            data-[side=left]:-translate-x-1
            data-[side=left]:slide-in-from-right-2
            data-[side=right]:translate-x-1
            data-[side=right]:slide-in-from-left-2
            data-[side=top]:-translate-y-1
            data-[side=top]:slide-in-from-bottom-2 data-open:animate-in
            data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out
            data-closed:fade-out-0 data-closed:zoom-out-95`,
            className,
          )}
          {...props}
        >
          <SelectScrollUpButton />
          <SelectPrimitive.List className="w-full min-w-(--anchor-width) p-1">
            {children}
          </SelectPrimitive.List>
          <SelectScrollDownButton />
        </SelectPrimitive.Popup>
      </SelectPrimitive.Positioner>
    </SelectPrimitive.Portal>
  );
}

function SelectLabel({
  className,
  ...props
}: ComponentProps<typeof SelectPrimitive.GroupLabel>) {
  return (
    <SelectPrimitive.GroupLabel
      className={cn('py-1.5 pr-2 pl-8 text-sm font-semibold', className)}
      {...props}
    />
  );
}

function SelectItem({
  className,
  children,
  ...props
}: ComponentProps<typeof SelectPrimitive.Item>) {
  return (
    <SelectPrimitive.Item
      className={cn(
        `relative flex w-full cursor-pointer items-center rounded-sm py-1.5 pr-2
        pl-8 text-sm outline-hidden select-none focus:bg-accent
        focus:text-accent-foreground data-disabled:pointer-events-none
        data-disabled:opacity-50`,
        className,
      )}
      {...props}
    >
      <span
        className="absolute left-2 flex size-3.5 items-center justify-center"
      >
        <SelectPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </SelectPrimitive.ItemIndicator>
      </span>

      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
}

function SelectSeparator({
  className,
  ...props
}: ComponentProps<typeof SelectPrimitive.Separator>) {
  return (
    <SelectPrimitive.Separator
      className={cn('-mx-1 my-1 h-px bg-muted', className)}
      {...props}
    />
  );
}

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
};
