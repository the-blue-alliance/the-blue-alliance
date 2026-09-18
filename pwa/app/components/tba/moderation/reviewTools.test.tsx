import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  OFFSEASON_DASHBOARD_URL,
  ReviewMediaTools,
  ReviewOffseasonTools,
  WEBCAST_DASHBOARD_URL,
  manageTeamMediaUrl,
} from '~/components/tba/moderation/reviewTools';

describe('ReviewOffseasonTools', () => {
  test('links to the Offseason Dashboard on the main site', () => {
    render(<ReviewOffseasonTools />);

    const link = screen.getByRole('link', { name: 'Offseason Dashboard' });
    expect(link.getAttribute('href')).toBe(OFFSEASON_DASHBOARD_URL);
    expect(OFFSEASON_DASHBOARD_URL).toBe(
      'https://www.thebluealliance.com/mod/offseasons',
    );
  });
});

describe('ReviewMediaTools', () => {
  test('links to the Webcast Dashboard on the main site', () => {
    render(<ReviewMediaTools />);

    const link = screen.getByRole('link', { name: 'Webcast Dashboard' });
    expect(link.getAttribute('href')).toBe(WEBCAST_DASHBOARD_URL);
    expect(WEBCAST_DASHBOARD_URL).toBe(
      'https://www.thebluealliance.com/mod/webcasts',
    );
  });

  test('Go has no destination until a team number is entered', () => {
    render(<ReviewMediaTools />);

    const go = screen.getByText('Go');
    expect(go.getAttribute('href')).toBeNull();

    fireEvent.change(screen.getByLabelText('Manage Team Media'), {
      target: { value: '254' },
    });

    const href = go.getAttribute('href') ?? '';
    expect(
      href.startsWith('https://www.thebluealliance.com/mod?team=254&year='),
    ).toBe(true);
    expect(href.endsWith('#frc254')).toBe(true);
  });
});

describe('manageTeamMediaUrl', () => {
  test('encodes the team number and jumps to the team tab', () => {
    expect(manageTeamMediaUrl('1124', 2026)).toBe(
      'https://www.thebluealliance.com/mod?team=1124&year=2026#frc1124',
    );
  });
});
