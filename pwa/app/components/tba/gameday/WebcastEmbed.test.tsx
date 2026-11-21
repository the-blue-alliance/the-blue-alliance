import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { WebcastEmbed } from '~/components/tba/gameday/WebcastEmbed';

describe('WebcastEmbed', () => {
  test('embeds a muted, autoplaying YouTube player', () => {
    render(<WebcastEmbed webcast={{ type: 'youtube', channel: 'abc123' }} />);

    expect(screen.getByTitle('YouTube video player').getAttribute('src')).toBe(
      'https://www.youtube.com/embed/abc123?autoplay=1&mute=1',
    );
  });

  test('embeds a muted Twitch player parented to this host', () => {
    render(
      <WebcastEmbed webcast={{ type: 'twitch', channel: 'firstinspires' }} />,
    );

    expect(screen.getByTitle('Twitch stream').getAttribute('src')).toBe(
      `https://player.twitch.tv/?channel=firstinspires&parent=${window.location.hostname}&muted=true`,
    );
  });

  test('explains that other providers are unsupported', () => {
    render(<WebcastEmbed webcast={{ type: 'livestream', channel: 'x' }} />);

    expect(
      screen.getByText('Webcast type "livestream" is not supported'),
    ).toBeTruthy();
    expect(
      screen.getByText('Only YouTube and Twitch webcasts are supported'),
    ).toBeTruthy();
  });
});
