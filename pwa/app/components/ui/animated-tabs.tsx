import { LayoutGroup, motion } from 'motion/react';
import {
  type ComponentProps,
  createContext,
  useContext,
  useState,
} from 'react';

import { Tabs, TabsTrigger } from '~/components/ui/tabs';
import { cn } from '~/lib/utils';

const AnimatedTabsContext = createContext<{ activeValue: string | undefined }>({
  activeValue: undefined,
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

  return (
    <AnimatedTabsContext.Provider value={{ activeValue }}>
      <LayoutGroup>
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
      </LayoutGroup>
    </AnimatedTabsContext.Provider>
  );
}

function AnimatedTabsTrigger({
  className,
  children,
  value,
  ...props
}: Omit<ComponentProps<typeof TabsTrigger>, 'value'> & { value: string }) {
  const { activeValue } = useContext(AnimatedTabsContext);
  const isActive = value !== undefined && activeValue === value;

  return (
    <TabsTrigger
      value={value}
      className={cn(
        'relative data-active:bg-transparent data-active:shadow-none',
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
}

export { AnimatedTabs, AnimatedTabsTrigger };
