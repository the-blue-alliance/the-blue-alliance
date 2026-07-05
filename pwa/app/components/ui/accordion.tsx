import { Accordion as AccordionPrimitive } from '@base-ui/react/accordion';

import ChevronDownIcon from '~icons/lucide/chevron-down';

import { cn } from '~/lib/utils';

function Accordion({
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Root>) {
  return <AccordionPrimitive.Root data-slot="accordion" {...props} />;
}

function AccordionItem({
  className,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Item>) {
  return (
    <AccordionPrimitive.Item
      data-slot="accordion-item"
      className={cn('border-b last:border-b-0', className)}
      {...props}
    />
  );
}

function AccordionTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Trigger>) {
  return (
    <AccordionPrimitive.Header className="flex">
      <AccordionPrimitive.Trigger
        data-slot="accordion-trigger"
        className={cn(
          `flex flex-1 cursor-pointer items-start justify-between gap-4
          rounded-md py-4 text-left text-sm font-medium transition-all
          outline-none hover:underline focus-visible:border-ring
          focus-visible:ring-[3px] focus-visible:ring-ring/50
          aria-disabled:pointer-events-none aria-disabled:opacity-50
          [&[data-panel-open]>svg]:rotate-180`,
          className,
        )}
        {...props}
      >
        {children}
        <ChevronDownIcon
          className="pointer-events-none size-4 shrink-0 translate-y-0.5
            text-muted-foreground transition-transform duration-200"
        />
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  );
}

function AccordionContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Panel>) {
  return (
    <AccordionPrimitive.Panel
      data-slot="accordion-content"
      className="overflow-hidden text-sm data-open:animate-accordion-down
        data-closed:animate-accordion-up"
      {...props}
    >
      <div className={cn('pt-0 pb-4', className)}>{children}</div>
    </AccordionPrimitive.Panel>
  );
}

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
