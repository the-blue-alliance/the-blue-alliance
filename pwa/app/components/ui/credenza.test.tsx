import { fireEvent, render, screen } from '@testing-library/react';
import { beforeAll, describe, expect, test, vi } from 'vitest';

import {
  Credenza,
  CredenzaBody,
  CredenzaClose,
  CredenzaContent,
  CredenzaDescription,
  CredenzaFooter,
  CredenzaHeader,
  CredenzaTitle,
  CredenzaTrigger,
} from '~/components/ui/credenza';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

beforeAll(() => {
  global.ResizeObserver = ResizeObserverMock;
});

function stubViewport(isDesktop: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn<(query: string) => Partial<MediaQueryList>>((query) => ({
      matches: isDesktop,
      media: query,
      onchange: null,
      addEventListener: vi.fn<() => void>(),
      removeEventListener: vi.fn<() => void>(),
      addListener: vi.fn<() => void>(),
      removeListener: vi.fn<() => void>(),
      dispatchEvent: vi.fn<() => boolean>(),
    })),
  );
}

function renderCredenza(props: {
  asChild?: true;
  focusContentOnOpen?: boolean;
  open?: boolean;
}) {
  const { asChild, focusContentOnOpen, open } = props;
  return render(
    <Credenza open={open}>
      <CredenzaTrigger asChild={asChild} className="group/trigger">
        {asChild ? <button type="button">Open</button> : 'Open'}
      </CredenzaTrigger>
      <CredenzaContent
        className="group/content"
        focusContentOnOpen={focusContentOnOpen}
      >
        <CredenzaHeader className="group/header">
          <CredenzaTitle className="group/title">Settings</CredenzaTitle>
          <CredenzaDescription className="group/description">
            Tweak things
          </CredenzaDescription>
        </CredenzaHeader>
        <CredenzaBody className="group/body">Body</CredenzaBody>
        <CredenzaFooter className="group/footer">
          <CredenzaClose asChild={asChild} className="group/close">
            {asChild ? <button type="button">Close me</button> : 'Close me'}
          </CredenzaClose>
        </CredenzaFooter>
      </CredenzaContent>
    </Credenza>,
  );
}

function expectSharedParts(dialog: HTMLElement) {
  expect(dialog.className).toContain('group/content');
  expect(screen.getByText('Settings').className).toContain('group/title');
  expect(screen.getByText('Settings').parentElement?.className).toContain(
    'group/header',
  );
  expect(screen.getByText('Tweak things').className).toContain(
    'group/description',
  );
  const body = screen.getByText('Body');
  expect(body.className).toContain('group/body');
  expect(body.className).toContain('px-4');
  expect(
    screen.getByRole('button', { name: 'Close me' }).parentElement?.className,
  ).toContain('group/footer');
}

describe('Credenza on desktop', () => {
  test('renders a dialog that opens from the trigger and closes from Close', async () => {
    stubViewport(true);
    renderCredenza({});

    const trigger = await screen.findByRole('button', { name: 'Open' });
    expect(trigger.getAttribute('data-slot')).toBe('dialog-trigger');
    expect(trigger.className).toContain('group/trigger');
    fireEvent.click(trigger);

    const dialog = await screen.findByRole('dialog');
    expect(dialog.getAttribute('data-slot')).toBe('dialog-content');
    expectSharedParts(dialog);
    const close = screen.getByRole('button', { name: 'Close me' });
    expect(close.getAttribute('data-slot')).toBe('dialog-close');
    expect(close.className).toContain('group/close');

    fireEvent.click(close);
    await vi.waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull();
    });
  });

  test('renders trigger and close through their child when asChild is set', async () => {
    stubViewport(true);
    renderCredenza({ asChild: true, focusContentOnOpen: true });

    const trigger = await screen.findByRole('button', { name: 'Open' });
    expect(trigger.getAttribute('data-slot')).toBe('dialog-trigger');
    fireEvent.click(trigger);

    const dialog = await screen.findByRole('dialog');
    await vi.waitFor(() => {
      expect(document.activeElement).toBe(dialog);
    });
    expect(
      screen
        .getByRole('button', { name: 'Close me' })
        .getAttribute('data-slot'),
    ).toBe('dialog-close');
  });
});

describe('Credenza on mobile', () => {
  test('renders a drawer that opens from the trigger and closes from Close', async () => {
    stubViewport(false);
    renderCredenza({});

    const trigger = screen.getByRole('button', { name: 'Open' });
    expect(trigger.getAttribute('data-slot')).toBeNull();
    expect(trigger.className).toContain('group/trigger');
    fireEvent.click(trigger);

    const dialog = await screen.findByRole('dialog');
    expect(dialog.getAttribute('data-vaul-drawer')).not.toBeNull();
    expectSharedParts(dialog);
    const close = screen.getByRole('button', { name: 'Close me' });
    expect(close.className).toContain('group/close');

    fireEvent.click(close);
    await vi.waitFor(() => {
      expect(screen.queryByRole('dialog')).toBeNull();
    });
  });

  test('focuses the drawer content itself when focusContentOnOpen is set', async () => {
    stubViewport(false);
    renderCredenza({ asChild: true, focusContentOnOpen: true, open: true });

    const dialog = await screen.findByRole('dialog');
    await vi.waitFor(() => {
      expect(document.activeElement).toBe(dialog);
    });
    expect(screen.getByRole('button', { name: 'Close me' })).toBeTruthy();
  });
});
