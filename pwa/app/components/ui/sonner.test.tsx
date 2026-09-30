import { render, screen } from '@testing-library/react';
import { toast } from 'sonner';
import { describe, expect, test, vi } from 'vitest';

import { Toaster } from '~/components/ui/sonner';

const { useThemeMock } = vi.hoisted(() => ({
  useThemeMock: vi.fn<() => { theme: 'dark' }>(() => ({ theme: 'dark' })),
}));

vi.mock('~/lib/theme', () => ({
  useTheme: useThemeMock,
}));

describe('Toaster', () => {
  test('renders toasts with the current theme, custom icons and forwarded props', async () => {
    const { container } = render(<Toaster position="top-center" />);
    expect(useThemeMock).toHaveBeenCalled();

    toast.success('Saved');

    const message = await screen.findByText('Saved');
    const toaster = container.querySelector('[data-sonner-toaster]');
    expect(toaster?.getAttribute('data-sonner-theme')).toBe('dark');
    expect(toaster?.getAttribute('data-x-position')).toBe('center');
    expect(toaster?.getAttribute('data-y-position')).toBe('top');
    expect(toaster?.className).toContain('toaster');

    const item = message.closest('[data-sonner-toast]');
    expect(item?.className).toContain('group-[.toaster]:!border-green-500');
    expect(item?.querySelector('svg')).not.toBeNull();
  });
});
