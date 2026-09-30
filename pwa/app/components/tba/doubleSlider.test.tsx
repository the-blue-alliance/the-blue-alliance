import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import { DoubleSlider } from '~/components/tba/doubleSlider';

function labels(container: HTMLElement) {
  return Array.from(container.querySelectorAll('span.text-sm')).map(
    (s) => s.textContent,
  );
}

beforeEach(() => {
  // See the last test: React warns about the stray minStepsBetweenThumbs prop.
  vi.spyOn(console, 'error').mockImplementation(() => {});
});

describe('DoubleSlider', () => {
  test('defaults to the full range and reports thumb changes', () => {
    const onValueChange = vi.fn<(values: number[]) => void>();
    const { container } = render(
      <DoubleSlider
        className="mt-7"
        min={2010}
        max={2026}
        step={1}
        minStepsBetweenThumbs={0}
        onValueChange={onValueChange}
      />,
    );
    expect(labels(container)).toEqual(['2010', '2026']);

    const [low] = screen.getAllByRole('slider', { hidden: true });
    fireEvent.keyDown(low, { key: 'ArrowRight' });
    expect(onValueChange).toHaveBeenCalledWith([2011, 2026]);
    expect(labels(container)).toEqual(['2011', '2026']);
  });

  test('uses a provided value, formats labels, and works without a handler', () => {
    const { container } = render(
      <DoubleSlider
        min={0}
        max={10}
        step={1}
        minStepsBetweenThumbs={0}
        value={[2, 8]}
        formatLabel={(v) => `Y${v}`}
      />,
    );
    expect(labels(container)).toEqual(['Y2', 'Y8']);
    const [, high] = screen.getAllByRole('slider', { hidden: true });
    fireEvent.keyDown(high, { key: 'ArrowLeft' });
    expect(labels(container)).toEqual(['Y2', 'Y7']);
  });

  test('forwards the Radix-era minStepsBetweenThumbs prop to the DOM', () => {
    // Base UI calls this `minStepsBetweenValues`; the old Radix prop name is
    // passed through untouched and ends up as a stray DOM attribute.
    const { container } = render(
      <DoubleSlider min={0} max={10} step={1} minStepsBetweenThumbs={2} />,
    );
    expect(
      container.firstElementChild?.getAttribute('minstepsbetweenthumbs'),
    ).toBe('2');
  });
});
