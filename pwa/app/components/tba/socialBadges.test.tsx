import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import type { Media, Webcast } from '~/api/tba/read';
import { MediaIcon, WebcastIcon } from '~/components/tba/socialBadges';

function media(type: Media['type'], foreignKey: string): Media {
  return { type, foreign_key: foreignKey, team_keys: ['frc254'] } as Media;
}

describe('MediaIcon', () => {
  test.each([
    ['youtube', 'https://www.youtube.com/handle'],
    ['youtube-channel', 'https://www.youtube.com/handle'],
    ['facebook-profile', 'https://www.facebook.com/handle'],
    ['github-profile', 'https://github.com/handle'],
    ['instagram-profile', 'https://www.instagram.com/handle'],
    ['twitter-profile', 'https://x.com/handle'],
    ['gitlab-profile', 'https://gitlab.com/handle'],
  ] as const)('links %s media', (type, href) => {
    render(<MediaIcon media={media(type, 'handle')} className="mt-7" />);
    expect(screen.getByRole('link', { name: 'handle' })).toHaveProperty(
      'href',
      href,
    );
  });

  test('renders nothing for other media types', () => {
    const { container } = render(<MediaIcon media={media('imgur', 'abc')} />);
    expect(container.innerHTML).toBe('');
  });
});

describe('WebcastIcon', () => {
  test.each([
    ['youtube', 'https://www.youtube.com/watch?v=chan', 'chan'],
    ['twitch', 'https://www.twitch.tv/chan', 'chan'],
    ['livestream', `${window.location.origin}/#`, 'livestream'],
  ] as const)('links a %s webcast', (type, href, label) => {
    render(
      <WebcastIcon
        webcast={{ type, channel: 'chan' } as Webcast}
        className="mt-7"
      />,
    );
    expect(screen.getByRole('link', { name: label })).toHaveProperty(
      'href',
      href,
    );
  });
});
