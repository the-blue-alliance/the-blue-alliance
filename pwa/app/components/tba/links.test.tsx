// @vitest-environment jsdom
import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { PitLocationLink } from '~/components/tba/links';

describe('PitLocationLink', () => {
  test('renders the pit location as a Nexus link', () => {
    render(
      <PitLocationLink
        teamNumber={254}
        year={2026}
        firstEventCode="cmptx"
        pitLocation="A1"
      />,
    );

    const link = screen.getByRole('link', { name: 'A1' });
    expect(link.getAttribute('href')).toBe(
      'https://frc.nexus/en/event/2026cmptx/team/254/map',
    );
  });
});
