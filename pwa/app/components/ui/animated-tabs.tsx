import { cn } from 'cn';
import {
  type ComponentProps,
  Suspense,
  createContext,
  lazy,
  useContext,
  useEffect,
  useState,
} from 'react';

import { Tabs, TabsTrigger } from '~/components/ui/tabs';

const AnimatedTabIndicator = lazy(
  () => import('~/components/ui/animatedTabIndicator'),
);

const AnimatedTabsContext = createContext<{
  activeValue: string | undefined;
  motionReady: boolean;
}>({
  activeValue: undefined,
  motionReady: false,
});

/**
 * True once the browser has had an idle moment after mount. The framer-motion
 * indicator chunk is only requested after that, so it is never on the
 * hydration critical path, deterministically rather than by timing luck.
 */
function useIdleAfterMount(): boolean {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (typeof window.requestIdleCallback === 'function') {
      const id = window.requestIdleCallback(() => setReady(true), {
        timeout: 2_000,
      });
      return () => window.cancelIdleCallback(id);
    }
    const id = window.setTimeout(() => setReady(true), 200);
    return () => window.clearTimeout(id);
  }, []);
  return ready;
}

type TabsChangeEventDetails = Parameters<
  NonNullable<ComponentProps<typeof Tabs>['onValueChange']>
>[1];

function AnimatedTabs({
  defaultValue,
  value,
  onValueChange,
  ...props
}: Omit<
  ComponentProps<typeof Tabs>,
  'defaultValue' | 'value' | 'onValueChange'
> & {
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string, eventDetails: TabsChangeEventDetails) => void;
}) {
  const [internalValue, setInternalValue] = useState<string | undefined>(
    value ?? defaultValue,
  );
  const activeValue = value ?? internalValue;
  const motionReady = useIdleAfterMount();

  return (
    <AnimatedTabsContext.Provider value={{ activeValue, motionReady }}>
      <Tabs
        defaultValue={defaultValue}
        value={value}
        onValueChange={(v, eventDetails) => {
          const stringValue = String(v);
          setInternalValue(stringValue);
          onValueChange?.(stringValue, eventDetails);
        }}
        {...props}
      />
    </AnimatedTabsContext.Provider>
  );
}

function AnimatedTabsTrigger({
  className,
  children,
  value,
  ...props
}: Omit<ComponentProps<typeof TabsTrigger>, 'value'> & { value: string }) {
  const { activeValue, motionReady } = useContext(AnimatedTabsContext);
  const isActive = value !== undefined && activeValue === value;
  const staticIndicator = (
    <span className="absolute inset-0 rounded-sm bg-background shadow-xs" />
  );

  return (
    <TabsTrigger
      value={value}
      className={cn(
        'relative data-active:bg-transparent data-active:shadow-none',
        className,
      )}
      {...props}
    >
      {isActive &&
        (motionReady ? (
          <Suspense fallback={staticIndicator}>
            <AnimatedTabIndicator />
          </Suspense>
        ) : (
          staticIndicator
        ))}
      <span className="relative z-10">{children}</span>
    </TabsTrigger>
  );
}

export { AnimatedTabs, AnimatedTabsTrigger };
