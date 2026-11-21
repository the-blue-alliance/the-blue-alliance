import { type JSX } from 'react';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';

const SHORTCUTS: { keys: string[]; action: string }[] = [
  { keys: ['j'], action: 'Focus the next suggestion' },
  { keys: ['k'], action: 'Focus the previous suggestion' },
  { keys: ['a'], action: 'Toggle accept on the focused suggestion' },
  { keys: ['r'], action: 'Toggle reject on the focused suggestion' },
  {
    keys: ['p'],
    action: 'Toggle "add as preferred" on the focused image (team media)',
  },
  { keys: ['?'], action: 'Show this dialog' },
];

function KeyChip({ children }: { children: string }): JSX.Element {
  return (
    <kbd
      className="inline-flex h-6 min-w-6 items-center justify-center rounded
        border bg-muted px-1.5 font-mono text-xs font-medium"
    >
      {children}
    </kbd>
  );
}

export function KeyboardShortcutsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}): JSX.Element {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Work the review queue without touching the mouse.
          </DialogDescription>
        </DialogHeader>
        <dl className="flex flex-col gap-2">
          {SHORTCUTS.map((shortcut) => (
            <div
              key={shortcut.action}
              className="flex items-center justify-between gap-4 text-sm"
            >
              <dd>{shortcut.action}</dd>
              <dt className="flex gap-1">
                {shortcut.keys.map((key) => (
                  <KeyChip key={key}>{key}</KeyChip>
                ))}
              </dt>
            </div>
          ))}
        </dl>
      </DialogContent>
    </Dialog>
  );
}
