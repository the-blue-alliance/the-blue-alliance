import { fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { describe, expect, test, vi } from 'vitest';

import {
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
} from '~/components/ui/dialog';

describe('Dialog', () => {
  test('opens from its trigger and renders header, footer and close button', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent className="group/content">
          <DialogHeader className="group/header">
            <DialogTitle className="group/title">Sign in</DialogTitle>
            <DialogDescription className="group/description">
              Use your account
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="group/footer">
            <DialogClose>Cancel</DialogClose>
          </DialogFooter>
        </DialogContent>
      </Dialog>,
    );

    expect(screen.queryByRole('dialog')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Open' }));

    const dialog = await screen.findByRole('dialog');
    expect(dialog.className).toContain('group/content');
    expect(dialog.getAttribute('data-slot')).toBe('dialog-content');
    expect(screen.getByText('Sign in').className).toContain('group/title');
    expect(screen.getByText('Use your account').className).toContain(
      'group/description',
    );
    expect(
      dialog.querySelector('[data-slot="dialog-header"]')?.className,
    ).toContain('group/header');
    expect(
      dialog.querySelector('[data-slot="dialog-footer"]')?.className,
    ).toContain('group/footer');
    expect(
      document.querySelector('[data-slot="dialog-overlay"]'),
    ).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Close' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    await vi.waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull();
    });
  });

  test('hides the close button when asked and forwards a ref object', () => {
    const ref = createRef<HTMLDivElement>();

    render(
      <Dialog open>
        <DialogContent ref={ref} showCloseButton={false}>
          <DialogTitle>Plain</DialogTitle>
        </DialogContent>
      </Dialog>,
    );

    expect(ref.current).toBe(screen.getByRole('dialog'));
    expect(screen.queryByRole('button', { name: 'Close' })).toBeNull();
  });

  test('forwards a callback ref and focuses the popup when focusContentOnOpen is set', async () => {
    const ref = vi.fn<(node: HTMLDivElement | null) => void>();

    render(
      <Dialog open>
        <DialogContent ref={ref} focusContentOnOpen>
          <DialogTitle>Focus me</DialogTitle>
          <button type="button">First</button>
        </DialogContent>
      </Dialog>,
    );

    const dialog = screen.getByRole('dialog');
    expect(ref).toHaveBeenCalledWith(dialog);
    await vi.waitFor(() => {
      expect(document.activeElement).toBe(dialog);
    });
  });

  test('prefers an explicit initialFocus over focusContentOnOpen', async () => {
    const initialFocus = createRef<HTMLButtonElement>();

    render(
      <Dialog open>
        <DialogContent focusContentOnOpen initialFocus={initialFocus}>
          <DialogTitle>Focus target</DialogTitle>
          <button type="button">First</button>
          <button type="button" ref={initialFocus}>
            Second
          </button>
        </DialogContent>
      </Dialog>,
    );

    await vi.waitFor(() => {
      expect(document.activeElement).toBe(
        screen.getByRole('button', { name: 'Second' }),
      );
    });
  });

  test('exposes overlay and portal wrappers with merged classes', () => {
    render(
      <Dialog open>
        <DialogPortal>
          <DialogOverlay className="group/overlay" />
        </DialogPortal>
      </Dialog>,
    );

    expect(
      document.querySelector('[data-slot="dialog-overlay"]')?.className,
    ).toContain('group/overlay');
  });
});
