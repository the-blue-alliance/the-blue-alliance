import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Avatar, AvatarFallback, AvatarImage } from '~/components/ui/avatar';

describe('Avatar', () => {
  test('shows the fallback until the image loads', () => {
    render(
      <Avatar className="group/avatar" data-testid="avatar">
        <AvatarImage
          className="group/image"
          src="https://example.com/avatar.png"
          alt="Team avatar"
        />
        <AvatarFallback className="group/fallback">254</AvatarFallback>
      </Avatar>,
    );

    const avatar = screen.getByTestId('avatar');
    expect(avatar.getAttribute('data-slot')).toBe('avatar');
    expect(avatar.className).toContain('group/avatar');

    // jsdom never loads images, so Base UI keeps rendering the fallback.
    const fallback = screen.getByText('254');
    expect(fallback.getAttribute('data-slot')).toBe('avatar-fallback');
    expect(fallback.className).toContain('group/fallback');
    expect(screen.queryByRole('img', { name: 'Team avatar' })).toBeNull();
  });
});
