import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  ReviewMediaTools,
  ReviewOffseasonTools,
  manageTeamMediaUrl,
} from '~/components/tba/moderation/reviewTools';

describe('ReviewOffseasonTools', () => {
  test('links to the Offseason Dashboard on the main site', () => {
    render(<ReviewOffseasonTools />);

    const link = screen.getByRole('link', { name: 'Offseason Dashboard' });
    expect(link.getAttribute('href')).toBe(
      'https://www.thebluealliance.com/mod/offseasons',
    );
  });
});

describe('ReviewMediaTools', () => {
  test('links to the Webcast Dashboard on the main site', () => {
    render(<ReviewMediaTools />);

    const link = screen.getByRole('link', { name: 'Webcast Dashboard' });
    expect(link.getAttribute('href')).toBe(
      'https://www.thebluealliance.com/mod/webcasts',
    );
  });

  test('Go has no destination until a team number is entered', () => {
    render(<ReviewMediaTools />);

    expect(screen.getByText('Go').getAttribute('href')).toBeNull();
  });

  test('Go links to the entered team on the main site', () => {
    render(<ReviewMediaTools />);

    fireEvent.change(screen.getByLabelText('Manage Team Media'), {
      target: { value: '254' },
    });

    const href = screen.getByText('Go').getAttribute('href') ?? '';
    expect(href).toMatch(
      /^https:\/\/www\.thebluealliance\.com\/mod\?team=254&year=\d{4}#frc254$/,
    );
  });
});

describe('manageTeamMediaUrl', () => {
  test('encodes the team number and jumps to the team tab', () => {
    expect(manageTeamMediaUrl('1124', 2026)).toBe(
      'https://www.thebluealliance.com/mod?team=1124&year=2026#frc1124',
    );
  });
});
