import { cn } from 'cn';
import {
  type ComponentProps,
  Suspense,
  createContext,
  lazy,
  useContext,
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
  // The framer-motion indicator (~60 KB) is only requested once the user
  // shows intent to switch tabs: a pointer entering the tab bar or focus
  // landing in it. That keeps it off the hydration critical path
  // deterministically, and it has usually arrived by the first click.
  const [motionReady, setMotionReady] = useState(false);
  const warmUp = () => setMotionReady(true);

  return (
    <AnimatedTabsContext.Provider value={{ activeValue, motionReady }}>
      <Tabs
        defaultValue={defaultValue}
        value={value}
        onValueChange={(v, eventDetails) => {
          const stringValue = String(v);
          setInternalValue(stringValue);
          warmUp();
          onValueChange?.(stringValue, eventDetails);
        }}
        onPointerEnter={warmUp}
        onFocusCapture={warmUp}
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
