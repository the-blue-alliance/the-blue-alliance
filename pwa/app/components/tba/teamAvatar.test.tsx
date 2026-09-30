import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import type { MediaAvatar } from '~/api/tba/read';
import TeamAvatar from '~/components/tba/teamAvatar';

const avatar = {
  type: 'avatar',
  foreign_key: 'avatar_2026_frc254',
  details: { base64Image: 'AAAA' },
} as MediaAvatar;

describe('TeamAvatar', () => {
  test('renders nothing without details', () => {
    const { container } = render(
      <TeamAvatar media={{ ...avatar, details: undefined } as MediaAvatar} />,
    );
    expect(container.innerHTML).toBe('');
  });

  test('toggles the accent color on click and keydown', () => {
    render(<TeamAvatar media={avatar} className="p-3" />);
    const img = screen.getByRole('img', { name: 'Team Avatar' });
    expect(img.getAttribute('src')).toBe('data:image/png;base64, AAAA');
    expect(img.className).toContain('bg-alliance-blue-accent');
    fireEvent.click(screen.getByRole('button'));
    expect(img.className).toContain('bg-alliance-red-accent');
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(img.className).toContain('bg-alliance-blue-accent');
  });

  test('starts red when requested', () => {
    render(<TeamAvatar media={avatar} defaultRed />);
    expect(screen.getByRole('img').className).toContain(
      'bg-alliance-red-accent',
    );
  });
});
