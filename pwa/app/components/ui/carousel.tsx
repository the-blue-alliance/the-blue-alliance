import { cn } from 'cn';
import {
  type Transition,
  motion,
  useMotionValue,
  useReducedMotion,
} from 'motion/react';
import {
  Children,
  type ReactNode,
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';

import ChevronLeftIcon from '~icons/lucide/chevron-left';
import ChevronRightIcon from '~icons/lucide/chevron-right';

interface CarouselContextType {
  index: number;
  setIndex: (newIndex: number) => void;
  itemsCount: number;
  setItemsCount: (newItemsCount: number) => void;
  disableDrag: boolean;
}

const CarouselContext = createContext<CarouselContextType | undefined>(
  undefined,
);

function useCarousel() {
  const context = useContext(CarouselContext);
  if (!context) {
    throw new Error('useCarousel must be used within a Carousel');
  }
  return context;
}

interface CarouselProps {
  children: ReactNode;
  className?: string;
  'aria-label': string;
  initialIndex?: number;
  index?: number;
  onIndexChange?: (newIndex: number) => void;
  disableDrag?: boolean;
}

function Carousel({
  children,
  className,
  'aria-label': ariaLabel,
  initialIndex = 0,
  index: externalIndex,
  onIndexChange,
  disableDrag = false,
}: CarouselProps) {
  const [internalIndex, setInternalIndex] = useState(initialIndex);
  const [itemsCount, setItemsCount] = useState(0);
  const isControlled = externalIndex !== undefined;
  const index = isControlled ? externalIndex : internalIndex;

  const setIndex = (newIndex: number) => {
    if (!isControlled) {
      setInternalIndex(newIndex);
    }
    onIndexChange?.(newIndex);
  };

  return (
    <CarouselContext.Provider
      value={{ index, setIndex, itemsCount, setItemsCount, disableDrag }}
    >
      <section
        aria-label={ariaLabel}
        aria-roledescription="carousel"
        className={cn('group/hover relative', className)}
      >
        <div className="overflow-hidden">{children}</div>
      </section>
    </CarouselContext.Provider>
  );
}

interface CarouselNavigationProps {
  className?: string;
  classNameButton?: string;
  alwaysShow?: boolean;
}

function CarouselNavigation({
  className,
  classNameButton,
  alwaysShow,
}: CarouselNavigationProps) {
  const { index, setIndex, itemsCount } = useCarousel();
  const buttonClassName = cn(
    `pointer-events-auto h-fit w-fit rounded-full bg-zinc-50 p-2
    transition-opacity duration-300 active:scale-97
    motion-safe:transition-[opacity,scale] dark:bg-zinc-950`,
    alwaysShow
      ? 'opacity-100'
      : `opacity-0 group-focus-within/hover:opacity-100
        group-hover/hover:opacity-100 pointer-coarse:opacity-100`,
    alwaysShow
      ? 'disabled:opacity-40'
      : `group-focus-within/hover:disabled:opacity-40
        group-hover/hover:disabled:opacity-40
        pointer-coarse:disabled:opacity-40`,
    classNameButton,
  );

  return (
    <div
      className={cn(
        `pointer-events-none absolute top-1/2 left-[-12.5%] flex w-[125%]
        -translate-y-1/2 justify-between px-2`,
        className,
      )}
    >
      <button
        type="button"
        aria-label="Previous slide"
        className={buttonClassName}
        disabled={index === 0}
        onClick={() => {
          if (index > 0) {
            setIndex(index - 1);
          }
        }}
      >
        <ChevronLeftIcon className="size-4 text-zinc-600 dark:text-zinc-50" />
      </button>
      <button
        type="button"
        aria-label="Next slide"
        className={buttonClassName}
        disabled={index + 1 === itemsCount}
        onClick={() => {
          if (index < itemsCount - 1) {
            setIndex(index + 1);
          }
        }}
      >
        <ChevronRightIcon className="size-4 text-zinc-600 dark:text-zinc-50" />
      </button>
    </div>
  );
}

interface CarouselIndicatorProps {
  className?: string;
  classNameButton?: string;
}

function CarouselIndicator({
  className,
  classNameButton,
}: CarouselIndicatorProps) {
  const { index, itemsCount, setIndex } = useCarousel();

  return (
    <div
      className={cn(
        'absolute bottom-0 z-10 flex w-full items-center justify-center',
        className,
      )}
    >
      <div className="flex space-x-2">
        {Array.from({ length: itemsCount }, (_, i) => (
          <button
            key={i}
            type="button"
            aria-label={`Go to slide ${i + 1}`}
            aria-current={index === i}
            onClick={() => setIndex(i)}
            className={cn(
              `h-2 w-2 rounded-full transition-opacity duration-300
              active:scale-97 motion-safe:transition-[opacity,scale]`,
              index === i
                ? 'bg-zinc-950 dark:bg-zinc-50'
                : 'bg-zinc-900/50 dark:bg-zinc-100/50',
              classNameButton,
            )}
          />
        ))}
      </div>
    </div>
  );
}

interface CarouselContentProps {
  children: ReactNode;
  className?: string;
  transition?: Transition;
}

function CarouselContent({
  children,
  className,
  transition,
}: CarouselContentProps) {
  const { index, setIndex, setItemsCount, disableDrag } = useCarousel();
  const [visibleItemsCount, setVisibleItemsCount] = useState(1);
  const dragX = useMotionValue(0);
  const reduceMotion = useReducedMotion();
  const containerRef = useRef<HTMLUListElement>(null);
  const itemsLength = Children.count(children);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        setVisibleItemsCount(
          entries.filter((entry) => entry.isIntersecting).length,
        );
      },
      { root: containerRef.current, threshold: 0.5 },
    );

    Array.from(containerRef.current.children).forEach((child) =>
      observer.observe(child),
    );

    return () => observer.disconnect();
  }, [children]);

  useEffect(() => {
    if (!itemsLength) {
      return;
    }

    setItemsCount(itemsLength);
  }, [itemsLength, setItemsCount]);

  const onDragEnd = () => {
    const x = dragX.get();

    if (x <= -10 && index < itemsLength - 1) {
      setIndex(index + 1);
    } else if (x >= 10 && index > 0) {
      setIndex(index - 1);
    }
  };

  return (
    <motion.ul
      drag={disableDrag ? false : 'x'}
      dragConstraints={disableDrag ? undefined : { left: 0, right: 0 }}
      dragMomentum={disableDrag ? undefined : false}
      style={{ x: disableDrag ? undefined : dragX }}
      animate={{ translateX: `-${index * (100 / visibleItemsCount)}%` }}
      onDragEnd={disableDrag ? undefined : onDragEnd}
      transition={
        reduceMotion
          ? { duration: 0 }
          : (transition ?? {
              damping: 18,
              stiffness: 90,
              type: 'spring',
              duration: 0.2,
            })
      }
      className={cn(
        'flex items-center',
        !disableDrag && 'cursor-grab active:cursor-grabbing',
        className,
      )}
      ref={containerRef}
    >
      {children}
    </motion.ul>
  );
}

interface CarouselItemProps {
  children: ReactNode;
  className?: string;
}

function CarouselItem({ children, className }: CarouselItemProps) {
  return (
    <motion.li
      aria-roledescription="slide"
      className={cn(
        'w-full min-w-0 shrink-0 grow-0 overflow-hidden',
        className,
      )}
    >
      {children}
    </motion.li>
  );
}

export {
  Carousel,
  CarouselContent,
  CarouselNavigation,
  CarouselIndicator,
  CarouselItem,
  useCarousel,
};
