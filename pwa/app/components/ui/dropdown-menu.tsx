import { Menu as DropdownMenuPrimitive } from '@base-ui/react/menu';
import { type ComponentProps, type HTMLAttributes } from 'react';

import CheckIcon from '~icons/lucide/check';
import ChevronRightIcon from '~icons/lucide/chevron-right';
import CircleIcon from '~icons/lucide/circle';

import { cn } from '~/lib/utils';

const DropdownMenu = DropdownMenuPrimitive.Root;

const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;

const DropdownMenuGroup = DropdownMenuPrimitive.Group;

const DropdownMenuPortal = DropdownMenuPrimitive.Portal;

const DropdownMenuSub = DropdownMenuPrimitive.SubmenuRoot;

const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup;

function DropdownMenuSubTrigger({
  className,
  inset,
  children,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.SubmenuTrigger> & {
  inset?: boolean;
}) {
  return (
    <DropdownMenuPrimitive.SubmenuTrigger
      className={cn(
        `flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm
        outline-hidden select-none focus:bg-accent data-popup-open:bg-accent`,
        inset && 'pl-8',
        className,
      )}
      {...props}
    >
      {children}
      <ChevronRightIcon className="ml-auto size-4" />
    </DropdownMenuPrimitive.SubmenuTrigger>
  );
}

function DropdownMenuContent({
  className,
  align,
  alignOffset,
  side,
  sideOffset = 4,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Popup> &
  Pick<
    ComponentProps<typeof DropdownMenuPrimitive.Positioner>,
    'align' | 'alignOffset' | 'side' | 'sideOffset'
  >) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Positioner
        align={align}
        alignOffset={alignOffset}
        side={side}
        sideOffset={sideOffset}
        className="isolate z-50 outline-none"
      >
        <DropdownMenuPrimitive.Popup
          className={cn(
            `z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1
            text-popover-foreground shadow-md
            data-[side=bottom]:slide-in-from-top-2
            data-[side=left]:slide-in-from-right-2
            data-[side=right]:slide-in-from-left-2
            data-[side=top]:slide-in-from-bottom-2 data-open:animate-in
            data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out
            data-closed:fade-out-0 data-closed:zoom-out-95`,
            className,
          )}
          {...props}
        />
      </DropdownMenuPrimitive.Positioner>
    </DropdownMenuPrimitive.Portal>
  );
}

function DropdownMenuSubContent({
  className,
  align = 'start',
  alignOffset = -3,
  side = 'right',
  sideOffset = 0,
  ...props
}: ComponentProps<typeof DropdownMenuContent>) {
  return (
    <DropdownMenuContent
      align={align}
      alignOffset={alignOffset}
      side={side}
      sideOffset={sideOffset}
      className={cn('w-auto', className)}
      {...props}
    />
  );
}

function DropdownMenuItem({
  className,
  inset,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Item> & {
  inset?: boolean;
}) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        `relative flex cursor-pointer items-center rounded-sm px-2 py-1.5
        text-sm outline-hidden transition-colors select-none focus:bg-accent
        focus:text-accent-foreground data-disabled:pointer-events-none
        data-disabled:opacity-50`,
        inset && 'pl-8',
        className,
      )}
      {...props}
    />
  );
}

function DropdownMenuCheckboxItem({
  className,
  children,
  checked,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.CheckboxItem>) {
  return (
    <DropdownMenuPrimitive.CheckboxItem
      className={cn(
        `relative flex cursor-pointer items-center rounded-sm py-1.5 pr-2 pl-8
        text-sm outline-hidden transition-colors select-none focus:bg-accent
        focus:text-accent-foreground data-disabled:pointer-events-none
        data-disabled:opacity-50`,
        className,
      )}
      checked={checked}
      {...props}
    >
      <span
        className="absolute left-2 flex size-3.5 items-center justify-center"
      >
        <DropdownMenuPrimitive.CheckboxItemIndicator>
          <CheckIcon className="size-4" />
        </DropdownMenuPrimitive.CheckboxItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.CheckboxItem>
  );
}

function DropdownMenuRadioItem({
  className,
  children,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.RadioItem>) {
  return (
    <DropdownMenuPrimitive.RadioItem
      className={cn(
        `relative flex cursor-pointer items-center rounded-sm py-1.5 pr-2 pl-8
        text-sm outline-hidden transition-colors select-none focus:bg-accent
        focus:text-accent-foreground data-disabled:pointer-events-none
        data-disabled:opacity-50`,
        className,
      )}
      {...props}
    >
      <span
        className="absolute left-2 flex size-3.5 items-center justify-center"
      >
        <DropdownMenuPrimitive.RadioItemIndicator>
          <CircleIcon className="size-2 fill-current" />
        </DropdownMenuPrimitive.RadioItemIndicator>
      </span>
      {children}
    </DropdownMenuPrimitive.RadioItem>
  );
}

function DropdownMenuLabel({
  className,
  inset,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.GroupLabel> & {
  inset?: boolean;
}) {
  return (
    <DropdownMenuPrimitive.GroupLabel
      className={cn(
        'px-2 py-1.5 text-sm font-semibold',
        inset && 'pl-8',
        className,
      )}
      {...props}
    />
  );
}

function DropdownMenuSeparator({
  className,
  ...props
}: ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
  return (
    <DropdownMenuPrimitive.Separator
      className={cn('-mx-1 my-1 h-px bg-muted', className)}
      {...props}
    />
  );
}

const DropdownMenuShortcut = ({
  className,
  ...props
}: HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      className={cn('ml-auto text-xs tracking-widest opacity-60', className)}
      {...props}
    />
  );
};
DropdownMenuShortcut.displayName = 'DropdownMenuShortcut';

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
};
