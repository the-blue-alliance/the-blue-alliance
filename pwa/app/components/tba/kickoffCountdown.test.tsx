import { act, render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { Temporal } from 'temporal-polyfill';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { KickoffCountdown } from '~/components/tba/kickoffCountdown';

vi.mock('@tanstack/react-router', () => ({
  ClientOnly: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

// Node ships a native Temporal that fake timers can't move, so targets are
// built relative to the real clock and only the interval is faked.
function kickoffIn(duration: Temporal.DurationLike): Temporal.ZonedDateTime {
  return Temporal.Now.zonedDateTimeISO('America/New_York').add(duration);
}

function unitValues() {
  return Array.from(document.querySelectorAll('.font-mono')).map(
    (el) => el.textContent,
  );
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['setInterval', 'clearInterval'] });
});

afterEach(() => {
  vi.useRealTimers();
});

describe('KickoffCountdown', () => {
  test('counts down to a kickoff more than a day away', () => {
    const kickoff = kickoffIn({ days: 2, hours: 3, minutes: 4, seconds: 30 });
    const { unmount } = render(
      <KickoffCountdown kickoffDateTimeEST={kickoff} />,
    );
    expect(
      screen.getByRole('heading', { name: `Kickoff ${kickoff.year}!` }),
    ).toBeTruthy();
    const [days, hours, minutes, seconds] = unitValues();
    expect([days, hours, minutes]).toEqual(['2', '03', '04']);
    expect(seconds).toMatch(/^\d\d$/);
    expect(screen.getByText('Days')).toBeTruthy();
    expect(screen.getByText('until Kickoff')).toBeTruthy();
    expect(screen.getByText(/Come back at/).textContent).toContain(
      kickoff.toLocaleString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }),
    );

    const watch = screen.getByRole('link', { name: 'Watch Kickoff Live' });
    expect(watch.getAttribute('aria-disabled')).toBe('true');
    expect(watch.getAttribute('tabindex')).toBe('-1');
    expect(
      screen.getByRole('link', { name: `${kickoff.year} FRC Game Resources` }),
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
    const kickoff = kickoffIn({ seconds: -10 });
    render(<KickoffCountdown kickoffDateTimeEST={kickoff} />);
    expect(
      screen.getByText(`Kickoff ${kickoff.year} is happening now!`),
    ).toBeTruthy();
    expect(unitValues()).toEqual([]);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(vi.getTimerCount()).toBe(0);
  });
});
