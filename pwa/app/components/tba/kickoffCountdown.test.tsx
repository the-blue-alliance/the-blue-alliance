import { act, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { Temporal } from 'temporal-polyfill';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { KickoffCountdown } from '~/components/tba/kickoffCountdown';

vi.mock('@tanstack/react-router', () => ({
  ClientOnly: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

const now = Temporal.Instant.from('2026-09-30T12:00:00Z');

function kickoffIn(duration: Temporal.DurationLike): Temporal.ZonedDateTime {
  return now.toZonedDateTimeISO('America/New_York').add(duration);
}

function unitValues() {
  return Array.from(document.querySelectorAll('.font-mono')).map(
    (el) => el.textContent,
  );
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
  vi.spyOn(Temporal.Now, 'instant').mockReturnValue(now);
  vi.spyOn(Temporal.Now, 'timeZoneId').mockReturnValue('Pacific/Auckland');
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('KickoffCountdown', () => {
  test('counts down to a kickoff more than a day away', () => {
    const kickoff = kickoffIn({ days: 2, hours: 3, minutes: 4, seconds: 30 });
    const { unmount } = render(
      <KickoffCountdown kickoffDateTimeEST={kickoff} />,
    );
    expect(screen.getByRole('heading', { name: 'Kickoff 2026!' })).toBeTruthy();
    expect(unitValues()).toEqual(['2', '03', '04', '30']);
    expect(screen.getByText('Days')).toBeTruthy();
    expect(screen.getByText('until Kickoff')).toBeTruthy();
    expect(screen.getByText(/Come back at/).textContent).toBe(
      'Come back at 4:04 AM GMT+13 on October 3, 2026 to watch live!',
    );

    const watch = screen.getByRole('link', { name: 'Watch Kickoff Live' });
    expect(watch.getAttribute('aria-disabled')).toBe('true');
    expect(watch.getAttribute('tabindex')).toBe('-1');
    expect(
      screen.getByRole('link', { name: '2026 FRC Game Resources' }),
    ).toBeTruthy();

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(unitValues()[0]).toBe('2');
    unmount();
  });

  test('enables the watch link within a day of kickoff', () => {
    render(<KickoffCountdown kickoffDateTimeEST={kickoffIn({ hours: 5 })} />);
    const watch = screen.getByRole('link', { name: 'Watch Kickoff Live' });
    expect(watch.getAttribute('aria-disabled')).toBe('false');
    expect(watch.getAttribute('tabindex')).toBeNull();
  });

  test('announces kickoff once it starts and stops ticking', () => {
    render(
      <KickoffCountdown kickoffDateTimeEST={kickoffIn({ seconds: -10 })} />,
    );
    expect(screen.getByText('Kickoff 2026 is happening now!')).toBeTruthy();
    expect(unitValues()).toEqual([]);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(vi.getTimerCount()).toBe(0);
  });
});
