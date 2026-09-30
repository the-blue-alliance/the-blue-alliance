import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Slider } from '~/components/ui/slider';

describe('Slider', () => {
  test('renders a slider with the given value and merged root class', () => {
    render(
      <Slider
        defaultValue={25}
        aria-label="Volume"
        className="group/slider"
        data-testid="slider"
      />,
    );

    // Base UI hides the thumb until it has measured the track, which jsdom
    // never does, so the range input is only reachable as a hidden element.
    const slider = screen.getByRole('slider', { hidden: true });
    expect(slider.getAttribute('aria-valuenow')).toBe('25');

    const root = screen.getByRole('group', { name: 'Volume' });
    expect(root).toBe(screen.getByTestId('slider'));
    expect(root.className).toContain('group/slider');
    expect(
      root.querySelector('[data-base-ui-slider-indicator]'),
    ).not.toBeNull();
  });
});
