import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import type { Event } from '~/api/tba/read';
import AddToCalendarLinks from '~/components/tba/addToCalendarLinks';

const event = {
  key: '2026miket',
  name: 'Kettering University Event #1',
  year: 2026,
  start_date: '2026-03-01',
  end_date: '2026-03-03',
  location_name: 'Kettering University',
  city: 'Flint',
  state_prov: 'MI',
  country: 'USA',
} as Event;

describe('AddToCalendarLinks', () => {
  test('offers Google, Apple, and Outlook calendar links', async () => {
    render(<AddToCalendarLinks event={event} />);

    fireEvent.click(screen.getByRole('button', { name: 'Add to calendar' }));

    const google = await screen.findByRole('menuitem', {
      name: 'Google Calendar',
    });
    expect(google.getAttribute('href')).toContain(
      'https://calendar.google.com/',
    );
    expect(google.getAttribute('target')).toBe('_blank');

    const apple = screen.getByRole('menuitem', { name: 'Apple Calendar' });
    expect(apple.getAttribute('href')).toMatch(/^data:text\/calendar/);
    expect(apple.getAttribute('download')).toBe('2026miket.ics');

    const outlook = screen.getByRole('menuitem', { name: 'Outlook' });
    expect(outlook.getAttribute('href')).toContain('outlook.live.com');
  });
});
