import * as TabsPrimitive from '@radix-ui/react-tabs';
import {
  type ComponentPropsWithoutRef,
  type ElementRef,
  forwardRef,
} from 'react';

import { cn } from '~/lib/utils';

const Tabs = TabsPrimitive.Root;

const TabsList = forwardRef<
  ElementRef<typeof TabsPrimitive.List>,
  ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      `inline-flex h-10 items-center justify-center rounded-md bg-muted p-1
      text-muted-foreground`,
      className,
    )}
    {...props}
  />
));
TabsList.displayName = TabsPrimitive.List.displayName;

const TabsTrigger = forwardRef<
  ElementRef<typeof TabsPrimitive.Trigger>,
  ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      `inline-flex cursor-pointer items-center justify-center rounded-sm px-5
      py-1.5 text-sm font-medium whitespace-nowrap ring-offset-background
      transition-all focus-visible:ring-2 focus-visible:ring-ring
      focus-visible:ring-offset-2 focus-visible:outline-hidden
      disabled:pointer-events-none disabled:opacity-50
      data-[state=active]:bg-background data-[state=active]:text-foreground
      data-[state=active]:shadow-xs`,
      className,
    )}
    {...props}
  />
));
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName;

const TabsContent = forwardRef<
  ElementRef<typeof TabsPrimitive.Content>,
  ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn('mt-2 focus-visible:outline-hidden', className)}
    {...props}
  />
));
TabsContent.displayName = TabsPrimitive.Content.displayName;

export { Tabs, TabsList, TabsTrigger, TabsContent };
