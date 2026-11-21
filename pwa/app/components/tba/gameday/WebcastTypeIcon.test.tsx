import { render } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { WebcastTypeIcon } from '~/components/tba/gameday/WebcastTypeIcon';

function iconClass(type: Parameters<typeof WebcastTypeIcon>[0]['type']) {
  const { container } = render(
    <WebcastTypeIcon type={type} className="size-5" />,
  );
  return container.querySelector('svg')?.getAttribute('class');
}

describe('WebcastTypeIcon', () => {
  test('uses the YouTube red for YouTube', () => {
    expect(iconClass('youtube')).toBe('text-red-600 size-5');
  });

  test('uses the Twitch purple for Twitch', () => {
    expect(iconClass('twitch')).toBe('text-purple-600 size-5');
  });

  test('falls back to a generic player icon for other providers', () => {
    expect(iconClass('livestream')).toBe('text-muted-foreground size-5');
  });
});
