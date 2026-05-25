import * as TabsPrimitive from '@radix-ui/react-tabs';
import { LayoutGroup, motion } from 'motion/react';
import {
  type ComponentPropsWithoutRef,
  type ElementRef,
  createContext,
  forwardRef,
  useContext,
  useState,
} from 'react';

import { Tabs, TabsTrigger } from '~/components/ui/tabs';
import { cn } from '~/lib/utils';

const AnimatedTabsContext = createContext<{ activeValue: string | undefined }>({
  activeValue: undefined,
});

const AnimatedTabs = forwardRef<
  ElementRef<typeof TabsPrimitive.Root>,
  ComponentPropsWithoutRef<typeof TabsPrimitive.Root>
>(({ defaultValue, value, onValueChange, ...props }, ref) => {
  const [internalValue, setInternalValue] = useState<string | undefined>(
    value ?? defaultValue,
  );
  const activeValue = value ?? internalValue;

  return (
    <AnimatedTabsContext.Provider value={{ activeValue }}>
      <LayoutGroup>
        <Tabs
          ref={ref}
          defaultValue={defaultValue}
          value={value}
          onValueChange={(v) => {
            setInternalValue(v);
            onValueChange?.(v);
          }}
          {...props}
        />
      </LayoutGroup>
    </AnimatedTabsContext.Provider>
  );
});
AnimatedTabs.displayName = 'AnimatedTabs';

const AnimatedTabsTrigger = forwardRef<
  ElementRef<typeof TabsPrimitive.Trigger>,
  ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, children, value, ...props }, ref) => {
  const { activeValue } = useContext(AnimatedTabsContext);
  const isActive = value !== undefined && activeValue === value;

  return (
    <TabsTrigger
      ref={ref}
      value={value}
      className={cn(
        `relative data-[state=active]:bg-transparent
        data-[state=active]:shadow-none`,
        className,
      )}
      {...props}
    >
      {isActive && (
        <motion.span
          layoutId="tab-indicator"
          initial={false}
          className="absolute inset-0 rounded-sm bg-background shadow-xs"
          transition={{ type: 'spring', bounce: 0.15, duration: 0.4 }}
        />
      )}
      <span className="relative z-10">{children}</span>
    </TabsTrigger>
  );
});
AnimatedTabsTrigger.displayName = 'AnimatedTabsTrigger';

export { AnimatedTabs, AnimatedTabsTrigger };
