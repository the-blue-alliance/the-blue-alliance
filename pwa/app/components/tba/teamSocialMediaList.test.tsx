import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import type { Media } from '~/api/tba/read';
import TeamSocialMediaList from '~/components/tba/teamSocialMediaList';

describe('TeamSocialMediaList', () => {
  test('renders socials sorted by type', () => {
    const socials = [
      { type: 'youtube-channel', foreign_key: 'yt', team_keys: [] },
      { type: 'facebook-profile', foreign_key: 'fb', team_keys: [] },
      { type: 'github-profile', foreign_key: 'gh', team_keys: [] },
    ] as unknown as Media[];
    render(<TeamSocialMediaList socials={socials} />);
    expect(screen.getAllByRole('link').map((l) => l.textContent)).toEqual([
      'fb',
      'gh',
      'yt',
    ]);
  });
});
