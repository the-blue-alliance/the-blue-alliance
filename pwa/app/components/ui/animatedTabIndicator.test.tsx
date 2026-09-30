import { render } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import AnimatedTabIndicator from '~/components/ui/animatedTabIndicator';

describe('AnimatedTabIndicator', () => {
  test('renders an absolutely positioned indicator span', () => {
    const { container } = render(<AnimatedTabIndicator />);

    const indicator = container.querySelector('span');
    expect(indicator?.className).toContain('absolute');
    expect(indicator?.className).toContain('bg-background');
  });
});
