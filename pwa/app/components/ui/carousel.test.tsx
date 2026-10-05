import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import {
  Carousel,
  CarouselContent,
  CarouselIndicator,
  CarouselItem,
  CarouselNavigation,
  useCarousel,
} from '~/components/ui/carousel';

class FakeIntersectionObserver {
  observe() {}
  disconnect() {}
}

beforeEach(() => {
  vi.stubGlobal('IntersectionObserver', FakeIntersectionObserver);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function TwoSlides({ index }: { index?: number }) {
  return (
    <Carousel aria-label="Robots" index={index}>
      <CarouselContent>
        <CarouselItem>One</CarouselItem>
        <CarouselItem>Two</CarouselItem>
      </CarouselContent>
      <CarouselNavigation />
      <CarouselIndicator />
    </Carousel>
  );
}

describe('Carousel', () => {
  test('exposes a region named by its label', () => {
    render(<TwoSlides />);

    expect(screen.getByRole('region', { name: 'Robots' })).toBeTruthy();
  });

  test('disables previous on the first slide', () => {
    render(<TwoSlides />);

    expect(
      screen.getByRole('button', { name: 'Previous slide' }),
    ).toHaveProperty('disabled', true);
  });

  test('disables next on the last slide after clicking next', () => {
    render(<TwoSlides />);

    fireEvent.click(screen.getByRole('button', { name: 'Next slide' }));

    expect(screen.getByRole('button', { name: 'Next slide' })).toHaveProperty(
      'disabled',
      true,
    );
  });

  test('marks the clicked dot as current', () => {
    render(<TwoSlides />);

    fireEvent.click(screen.getByRole('button', { name: 'Go to slide 2' }));

    expect(
      screen
        .getByRole('button', { name: 'Go to slide 2' })
        .getAttribute('aria-current'),
    ).toBe('true');
  });

  test('starts at the slide given by a controlled index', () => {
    render(<TwoSlides index={1} />);

    expect(
      screen.getByRole('button', { name: 'Previous slide' }),
    ).toHaveProperty('disabled', false);
  });

  test('useCarousel throws outside a Carousel', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    function Orphan() {
      useCarousel();
      return null;
    }

    expect(() => render(<Orphan />)).toThrow(
      'useCarousel must be used within a Carousel',
    );
  });
});
