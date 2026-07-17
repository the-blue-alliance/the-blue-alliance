import { Dialog as DialogPrimitive } from '@base-ui/react/dialog';
import { useRef } from 'react';

import XIcon from '~icons/lucide/x';

import { cn } from '~/lib/utils';

function Dialog({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />;
}

function DialogTrigger({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />;
}

function DialogPortal({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />;
}

function DialogClose({
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />;
}

function DialogOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Backdrop>) {
  return (
    <DialogPrimitive.Backdrop
      data-slot="dialog-overlay"
      className={cn(
        `fixed inset-0 z-50 bg-black/50 dark:bg-black/75 data-open:animate-in
        data-open:fade-in-0 data-closed:animate-out data-closed:fade-out-0
        data-closed:fill-mode-forwards`,
        className,
      )}
      {...props}
    />
  );
}

function DialogContent({
  className,
  children,
  showCloseButton = true,
  focusContentOnOpen = false,
  initialFocus,
  ref,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Popup> & {
  showCloseButton?: boolean;
  /**
   * Focus the popup container itself when the dialog opens instead of Base
   * UI's default (the first tabbable element inside the popup). Ignored
   * when an explicit `initialFocus` is passed.
   */
  focusContentOnOpen?: boolean;
}) {
  const popupRef = useRef<HTMLDivElement | null>(null);

  return (
    <DialogPortal data-slot="dialog-portal">
      <DialogOverlay />
      <DialogPrimitive.Popup
        data-slot="dialog-content"
        ref={(node) => {
          popupRef.current = node;
          if (typeof ref === 'function') {
            ref(node);
          } else if (ref) {
            ref.current = node;
          }
        }}
        initialFocus={
          initialFocus ?? (focusContentOnOpen ? popupRef : undefined)
        }
        className={cn(
          `fixed top-[50%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)]
          translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border
          bg-background p-6 shadow-lg duration-200 sm:max-w-lg
          data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95
          data-closed:animate-out data-closed:fade-out-0
          data-closed:fill-mode-forwards data-closed:zoom-out-95`,
          className,
        )}
        {...props}
      >
        {children}
        {showCloseButton && (
          <DialogPrimitive.Close
            data-slot="dialog-close"
            className="absolute top-4 right-4 cursor-pointer rounded-xs
              opacity-70 ring-offset-background transition-opacity
              hover:opacity-100 focus:ring-2 focus:ring-ring focus:ring-offset-2
              focus:outline-hidden disabled:pointer-events-none
              data-[state=open]:bg-accent
              data-[state=open]:text-muted-foreground
              [&_svg]:pointer-events-none [&_svg]:shrink-0
              [&_svg:not([class*='size-'])]:size-4"
          >
            <XIcon />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Popup>
    </DialogPortal>
  );
}

function DialogHeader({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="dialog-header"
      className={cn('flex flex-col gap-2 text-center sm:text-left', className)}
      {...props}
    />
  );
}

function DialogFooter({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <div
      data-slot="dialog-footer"
      className={cn(
        'flex flex-col-reverse gap-2 sm:flex-row sm:justify-end',
        className,
      )}
      {...props}
    />
  );
}

function DialogTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn('text-lg leading-none font-semibold', className)}
      {...props}
    />
  );
}

function DialogDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  );
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
};
