import { Tabs as TabsPrimitive } from '@base-ui/react/tabs';
import { type ComponentProps } from 'react';

import { cn } from '~/lib/utils';

const Tabs = TabsPrimitive.Root;

function TabsList({
  className,
  ...props
}: ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      className={cn(
        `inline-flex h-10 items-center justify-center rounded-md bg-muted p-1
        text-muted-foreground`,
        className,
      )}
      {...props}
    />
  );
}

function TabsTrigger({
  className,
  ...props
}: ComponentProps<typeof TabsPrimitive.Tab>) {
  return (
    <TabsPrimitive.Tab
      className={cn(
        `inline-flex cursor-pointer items-center justify-center rounded-sm px-5
        py-1.5 text-sm font-medium whitespace-nowrap ring-offset-background
        transition-all focus-visible:ring-2 focus-visible:ring-ring
        focus-visible:ring-offset-2 focus-visible:outline-hidden
        disabled:pointer-events-none disabled:opacity-50
        data-active:bg-background data-active:text-foreground
        data-active:shadow-xs`,
        className,
      )}
      {...props}
    />
  );
}

function TabsContent({
  className,
  ...props
}: ComponentProps<typeof TabsPrimitive.Panel>) {
  return (
    <TabsPrimitive.Panel
      className={cn('mt-2 focus-visible:outline-hidden', className)}
      {...props}
    />
  );
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
