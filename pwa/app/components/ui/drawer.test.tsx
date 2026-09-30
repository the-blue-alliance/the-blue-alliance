import { fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { beforeAll, beforeEach, describe, expect, test, vi } from 'vitest';

import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  DrawerPortal,
  DrawerTitle,
  DrawerTrigger,
} from '~/components/ui/drawer';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

beforeEach(() => {
  // vaul checks the pointer type through matchMedia, which jsdom lacks.
  vi.stubGlobal(
    'matchMedia',
    vi.fn<(query: string) => Partial<MediaQueryList>>((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn<() => void>(),
      removeEventListener: vi.fn<() => void>(),
      addListener: vi.fn<() => void>(),
      removeListener: vi.fn<() => void>(),
      dispatchEvent: vi.fn<() => boolean>(),
    })),
  );
});

describe('Drawer', () => {
  test('opens from its trigger with handle, header, footer and close', async () => {
    const contentRef = createRef<HTMLDivElement>();
    const titleRef = createRef<HTMLHeadingElement>();
    const descriptionRef = createRef<HTMLParagraphElement>();

    render(
      <Drawer>
        <DrawerTrigger>Open drawer</DrawerTrigger>
        <DrawerContent ref={contentRef} className="group/content">
          <DrawerHeader className="group/header">
            <DrawerTitle ref={titleRef} className="group/title">
              Filters
            </DrawerTitle>
            <DrawerDescription
              ref={descriptionRef}
              className="group/description"
            >
              Narrow the list
            </DrawerDescription>
          </DrawerHeader>
          <DrawerFooter className="group/footer">
            <DrawerClose>Done</DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>,
    );

    expect(screen.queryByRole('dialog')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Open drawer' }));

    const dialog = await screen.findByRole('dialog');
    expect(contentRef.current).toBe(dialog);
    expect(dialog.className).toContain('group/content');
    expect(dialog.querySelector('.rounded-full.bg-muted')).not.toBeNull();

    expect(titleRef.current).toBe(screen.getByText('Filters'));
    expect(titleRef.current?.className).toContain('group/title');
    expect(descriptionRef.current).toBe(screen.getByText('Narrow the list'));
    expect(descriptionRef.current?.className).toContain('group/description');
    expect(screen.getByText('Filters').parentElement?.className).toContain(
      'group/header',
    );
    expect(
      screen.getByRole('button', { name: 'Done' }).parentElement?.className,
    ).toContain('group/footer');
    expect(document.querySelector('[data-vaul-overlay]')).not.toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Done' }));
    await vi.waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull();
    });
  });

  test('can hide the drag handle and disable background scaling', () => {
    render(
      <Drawer open shouldScaleBackground={false}>
        <DrawerContent showHandle={false}>
          <DrawerTitle>No handle</DrawerTitle>
        </DrawerContent>
      </Drawer>,
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog.querySelector('.rounded-full.bg-muted')).toBeNull();
  });

  test('exposes the overlay and portal with merged classes', () => {
    const overlayRef = createRef<HTMLDivElement>();

    render(
      <Drawer open>
        <DrawerPortal>
          <DrawerOverlay ref={overlayRef} className="group/overlay" />
        </DrawerPortal>
      </Drawer>,
    );

    expect(overlayRef.current?.className).toContain('group/overlay');
    expect(overlayRef.current?.className).toContain('fixed');
  });
});
