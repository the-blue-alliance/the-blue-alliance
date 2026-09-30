import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import {
  AnimatedTabs,
  AnimatedTabsTrigger,
} from '~/components/ui/animated-tabs';
import { TabsContent, TabsList } from '~/components/ui/tabs';

function indicatorIn(tab: HTMLElement) {
  return tab.querySelector('span.absolute');
}

describe('AnimatedTabs', () => {
  test('uncontrolled: shows the indicator on the default tab and moves it on click', async () => {
    const onValueChange = vi.fn<(value: string) => void>();

    render(
      <AnimatedTabs defaultValue="results" onValueChange={onValueChange}>
        <TabsList>
          <AnimatedTabsTrigger value="results" className="group/trigger">
            Results
          </AnimatedTabsTrigger>
          <AnimatedTabsTrigger value="rankings">Rankings</AnimatedTabsTrigger>
        </TabsList>
        <TabsContent value="results">Results panel</TabsContent>
        <TabsContent value="rankings">Rankings panel</TabsContent>
      </AnimatedTabs>,
    );

    const results = screen.getByRole('tab', { name: 'Results' });
    const rankings = screen.getByRole('tab', { name: 'Rankings' });
    expect(results.className).toContain('group/trigger');
    expect(indicatorIn(results)).not.toBeNull();
    expect(indicatorIn(rankings)).toBeNull();

    fireEvent.click(rankings);

    expect(onValueChange).toHaveBeenCalledWith('rankings', expect.anything());
    expect(indicatorIn(rankings)).not.toBeNull();
    expect(indicatorIn(results)).toBeNull();
    expect(screen.getByText('Rankings panel')).toBeTruthy();

    // The lazy motion-backed indicator eventually replaces the fallback.
    await vi.waitFor(() => {
      expect(indicatorIn(rankings)?.className).toContain('shadow-xs');
    });
  });

  test('controlled: the indicator follows the value prop, not clicks', () => {
    const onValueChange = vi.fn<(value: string) => void>();

    const { rerender } = render(
      <AnimatedTabs value="results" onValueChange={onValueChange}>
        <TabsList>
          <AnimatedTabsTrigger value="results">Results</AnimatedTabsTrigger>
          <AnimatedTabsTrigger value="rankings">Rankings</AnimatedTabsTrigger>
        </TabsList>
      </AnimatedTabs>,
    );

    fireEvent.click(screen.getByRole('tab', { name: 'Rankings' }));

    expect(onValueChange).toHaveBeenCalledWith('rankings', expect.anything());
    expect(
      indicatorIn(screen.getByRole('tab', { name: 'Results' })),
    ).not.toBeNull();
    expect(
      indicatorIn(screen.getByRole('tab', { name: 'Rankings' })),
    ).toBeNull();

    rerender(
      <AnimatedTabs value="rankings" onValueChange={onValueChange}>
        <TabsList>
          <AnimatedTabsTrigger value="results">Results</AnimatedTabsTrigger>
          <AnimatedTabsTrigger value="rankings">Rankings</AnimatedTabsTrigger>
        </TabsList>
      </AnimatedTabs>,
    );

    expect(
      indicatorIn(screen.getByRole('tab', { name: 'Rankings' })),
    ).not.toBeNull();
  });

  test('without a value, Base UI selects the first tab and the indicator follows it', () => {
    render(
      <AnimatedTabs>
        <TabsList>
          <AnimatedTabsTrigger value="results">Results</AnimatedTabsTrigger>
          <AnimatedTabsTrigger value="rankings">Rankings</AnimatedTabsTrigger>
        </TabsList>
      </AnimatedTabs>,
    );

    const results = screen.getByRole('tab', { name: 'Results' });
    const rankings = screen.getByRole('tab', { name: 'Rankings' });
    expect(results.getAttribute('aria-selected')).toBe('true');
    expect(indicatorIn(results)).not.toBeNull();

    // No onValueChange handler is wired, so this covers the optional call.
    fireEvent.click(rankings);

    expect(indicatorIn(rankings)).not.toBeNull();
    expect(indicatorIn(results)).toBeNull();
  });
});
