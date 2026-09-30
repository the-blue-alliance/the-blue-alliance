import { act, fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { beforeEach, describe, expect, test, vi } from 'vitest';

import {
  Carousel,
  type CarouselApi,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '~/components/ui/carousel';

type Listener = (api?: CarouselApi) => void;

interface FakeApi {
  listeners: Record<string, Listener[]>;
  canScrollPrev: () => boolean;
  canScrollNext: () => boolean;
  scrollPrev: () => void;
  scrollNext: () => void;
  on: (event: string, listener: Listener) => void;
  off: (event: string, listener: Listener) => void;
}

const { embla } = vi.hoisted(() => ({
  embla: {
    api: undefined as FakeApi | undefined,
    useEmblaCarousel:
      vi.fn<() => [(node: HTMLElement | null) => void, unknown]>(),
    viewportRef: vi.fn<(node: HTMLElement | null) => void>(),
  },
}));

vi.mock('embla-carousel-react', () => ({
  default: embla.useEmblaCarousel,
}));

function makeApi(state: { prev: boolean; next: boolean }) {
  const listeners: Record<string, Listener[]> = {};
  return {
    listeners,
    canScrollPrev: vi.fn<() => boolean>(() => state.prev),
    canScrollNext: vi.fn<() => boolean>(() => state.next),
    scrollPrev: vi.fn<() => void>(),
    scrollNext: vi.fn<() => void>(),
    on: vi.fn<(event: string, listener: Listener) => void>(
      (event, listener) => {
        listeners[event] = [...(listeners[event] ?? []), listener];
      },
    ),
    off: vi.fn<(event: string, listener: Listener) => void>(
      (event, listener) => {
        listeners[event] = (listeners[event] ?? []).filter(
          (l) => l !== listener,
        );
      },
    ),
  };
}

function renderCarousel(
  props: Partial<React.ComponentProps<typeof Carousel>> = {},
) {
  return render(
    <Carousel {...props}>
      <CarouselContent className="group/content" data-testid="content">
        <CarouselItem className="group/item">Slide 1</CarouselItem>
        <CarouselItem>Slide 2</CarouselItem>
      </CarouselContent>
      <CarouselPrevious className="group/prev" />
      <CarouselNext className="group/next" />
    </Carousel>,
  );
}

beforeEach(() => {
  embla.api = undefined;
  embla.useEmblaCarousel.mockImplementation(() => [
    embla.viewportRef,
    embla.api,
  ]);
});

describe('Carousel', () => {
  test('before embla initialises, both buttons are disabled and keys are inert', () => {
    const setApi = vi.fn<(api: CarouselApi) => void>();
    renderCarousel({ setApi });

    const region = screen.getByRole('region');
    expect(region.getAttribute('aria-roledescription')).toBe('carousel');
    expect(embla.useEmblaCarousel).toHaveBeenCalledWith(
      { axis: 'x' },
      undefined,
    );

    const prev = screen.getByRole('button', { name: 'Previous slide' });
    const next = screen.getByRole('button', { name: 'Next slide' });
    expect(prev.hasAttribute('disabled')).toBe(true);
    expect(next.hasAttribute('disabled')).toBe(true);
    expect(prev.className).toContain('group/prev');
    expect(next.className).toContain('group/next');

    fireEvent.keyDown(region, { key: 'ArrowLeft' });
    fireEvent.keyDown(region, { key: 'ArrowRight' });
    expect(setApi).not.toHaveBeenCalled();
  });

  test('horizontal layout classes and forwarded refs', () => {
    const ref = createRef<HTMLDivElement>();
    const contentRef = createRef<HTMLDivElement>();
    const itemRef = createRef<HTMLDivElement>();

    render(
      <Carousel ref={ref} className="group/carousel">
        <CarouselContent ref={contentRef} className="group/content">
          <CarouselItem ref={itemRef} className="group/item">
            Slide
          </CarouselItem>
        </CarouselContent>
      </Carousel>,
    );

    expect(ref.current).toBe(screen.getByRole('region'));
    expect(ref.current?.className).toContain('group/carousel');
    expect(contentRef.current?.className).toContain('-ml-4');
    expect(contentRef.current?.className).toContain('group/content');
    expect(contentRef.current?.parentElement?.className).toContain(
      'overflow-hidden',
    );
    expect(embla.viewportRef).toHaveBeenCalled();

    const item = screen.getByRole('group', { name: '' });
    expect(itemRef.current).toBe(item);
    expect(item.getAttribute('aria-roledescription')).toBe('slide');
    expect(item.className).toContain('pl-4');
    expect(item.className).toContain('group/item');
  });

  test('vertical orientation flips the axis and layout classes', () => {
    const plugins: never[] = [];
    renderCarousel({ orientation: 'vertical', opts: { loop: true }, plugins });

    expect(embla.useEmblaCarousel).toHaveBeenCalledWith(
      { loop: true, axis: 'y' },
      plugins,
    );
    expect(screen.getByTestId('content').className).toContain('flex-col');
    expect(screen.getByText('Slide 1').className).toContain('pt-4');
    expect(
      screen.getByRole('button', { name: 'Previous slide' }).className,
    ).toContain('rotate-90');
    expect(
      screen.getByRole('button', { name: 'Next slide' }).className,
    ).toContain('-bottom-12');
  });

  test('once embla is ready, buttons and arrow keys drive it and state tracks select events', () => {
    const state = { prev: false, next: true };
    const api = makeApi(state);
    embla.api = api;
    const setApi = vi.fn<(api: CarouselApi) => void>();

    const { unmount } = renderCarousel({ setApi });

    expect(setApi).toHaveBeenCalledWith(api);
    expect(api.on).toHaveBeenCalledWith('reInit', expect.any(Function));
    expect(api.on).toHaveBeenCalledWith('select', expect.any(Function));

    const prev = screen.getByRole('button', { name: 'Previous slide' });
    const next = screen.getByRole('button', { name: 'Next slide' });
    expect(prev.hasAttribute('disabled')).toBe(true);
    expect(next.hasAttribute('disabled')).toBe(false);

    fireEvent.click(next);
    expect(api.scrollNext).toHaveBeenCalledTimes(1);

    const region = screen.getByRole('region');
    fireEvent.keyDown(region, { key: 'ArrowRight' });
    expect(api.scrollNext).toHaveBeenCalledTimes(2);
    fireEvent.keyDown(region, { key: 'ArrowLeft' });
    expect(api.scrollPrev).toHaveBeenCalledTimes(1);
    fireEvent.keyDown(region, { key: 'Enter' });
    expect(api.scrollPrev).toHaveBeenCalledTimes(1);
    expect(api.scrollNext).toHaveBeenCalledTimes(2);

    // Simulate embla reaching the last slide.
    state.prev = true;
    state.next = false;
    act(() => {
      for (const listener of api.listeners.select) {
        listener(api as unknown as CarouselApi);
      }
    });
    expect(prev.hasAttribute('disabled')).toBe(false);
    expect(next.hasAttribute('disabled')).toBe(true);

    fireEvent.click(prev);
    expect(api.scrollPrev).toHaveBeenCalledTimes(2);

    // The select handler guards against a missing api and leaves state alone.
    act(() => {
      for (const listener of api.listeners.select) {
        listener(undefined);
      }
    });
    expect(prev.hasAttribute('disabled')).toBe(false);

    unmount();
    expect(api.off).toHaveBeenCalledWith('select', expect.any(Function));
  });

  test('sub-components throw outside a Carousel', () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    expect(() => render(<CarouselContent />)).toThrow(
      'useCarousel must be used within a <Carousel />',
    );
  });
});
