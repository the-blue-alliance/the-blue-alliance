import * as NavigationMenuPrimitive from '@radix-ui/react-navigation-menu';

import { cn } from '~/lib/utils';

function NavigationMenu({
  className,
  children,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Root>) {
  return (
    <NavigationMenuPrimitive.Root
      data-slot="navigation-menu"
      className={cn('group/navigation-menu relative', className)}
      data-viewport={true}
      {...props}
    >
      {children}
    </NavigationMenuPrimitive.Root>
  );
}

function NavigationMenuList({
  className,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.List>) {
  return (
    <NavigationMenuPrimitive.List
      data-slot="navigation-menu-list"
      className={cn(
        // 'group flex flex-1 list-none items-center justify-center gap-1',
        className,
      )}
      {...props}
    />
  );
}

function NavigationMenuItem({
  className,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Item>) {
  return (
    <NavigationMenuPrimitive.Item
      data-slot="navigation-menu-item"
      className={cn('relative', className)}
      {...props}
    />
  );
}

function NavigationMenuTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Trigger>) {
  return (
    <NavigationMenuPrimitive.Trigger
      data-slot="navigation-menu-trigger"
      className={cn(
        `group cursor-pointer rounded-full p-2 text-white transition-colors
        duration-200 hover:bg-black/20`,
        className,
      )}
      {...props}
    >
      {children}
    </NavigationMenuPrimitive.Trigger>
  );
}

function NavigationMenuContent({
  className,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Content>) {
  return (
    <NavigationMenuPrimitive.Content
      data-slot="navigation-menu-content"
      className={cn(
        'top-0 left-0 w-full p-2 pr-2.5 md:w-auto',
        `group-data-[viewport=false]/navigation-menu:top-full
        group-data-[viewport=false]/navigation-menu:mt-1.5
        group-data-[viewport=false]/navigation-menu:overflow-hidden
        group-data-[viewport=false]/navigation-menu:rounded-md
        group-data-[viewport=false]/navigation-menu:border
        group-data-[viewport=false]/navigation-menu:bg-popover
        group-data-[viewport=false]/navigation-menu:text-popover-foreground
        group-data-[viewport=false]/navigation-menu:shadow
        group-data-[viewport=false]/navigation-menu:duration-200
        **:data-[slot=navigation-menu-link]:focus:ring-0
        **:data-[slot=navigation-menu-link]:focus:outline-none
        group-data-[viewport=false]/navigation-menu:data-[state=closed]:animate-out
        group-data-[viewport=false]/navigation-menu:data-[state=closed]:fade-out-0
        group-data-[viewport=false]/navigation-menu:data-[state=closed]:zoom-out-95
        group-data-[viewport=false]/navigation-menu:data-[state=open]:animate-in
        group-data-[viewport=false]/navigation-menu:data-[state=open]:fade-in-0
        group-data-[viewport=false]/navigation-menu:data-[state=open]:zoom-in-95`,
        className,
      )}
      {...props}
    />
  );
}

function NavigationMenuViewport({
  className,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Viewport>) {
  return (
    <div
      className={cn(
        'absolute inset-x-0 top-full isolate z-50 flex justify-center',
      )}
    >
      <NavigationMenuPrimitive.Viewport
        data-slot="navigation-menu-viewport"
        className={cn(
          `origin-top-center relative
          h-(--radix-navigation-menu-viewport-height) w-full overflow-hidden
          rounded-b-xl bg-primary text-white
          md:w-(--radix-navigation-menu-viewport-width)`,
          className,
        )}
        {...props}
      />
    </div>
  );
}

function NavigationMenuLink({
  className,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Link>) {
  return (
    <NavigationMenuPrimitive.Link
      data-slot="navigation-menu-link"
      className={cn(
        `flex gap-1 rounded-md p-2 text-sm leading-4 transition-all outline-none
        hover:bg-accent hover:text-accent-foreground focus-visible:ring-[3px]
        focus-visible:ring-ring/50 focus-visible:outline-1
        data-[active=true]:bg-accent/50
        data-[active=true]:text-accent-foreground
        data-[active=true]:hover:bg-accent data-[active=true]:focus:bg-accent
        [&_svg:not([class*='size-'])]:size-4
        [&_svg:not([class*='text-'])]:text-muted-foreground`,
        className,
      )}
      {...props}
    />
  );
}

function NavigationMenuIndicator({
  className,
  ...props
}: React.ComponentProps<typeof NavigationMenuPrimitive.Indicator>) {
  return (
    <NavigationMenuPrimitive.Indicator
      data-slot="navigation-menu-indicator"
      className={cn(
        `top-full z-[1] flex h-1.5 items-end justify-center overflow-hidden
        data-[state=hidden]:animate-out data-[state=hidden]:fade-out
        data-[state=visible]:animate-in data-[state=visible]:fade-in`,
        className,
      )}
      {...props}
    >
      <div
        className="relative top-[60%] h-2 w-2 rotate-45 rounded-tl-sm bg-border
          shadow-md"
      />
    </NavigationMenuPrimitive.Indicator>
  );
}

export {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuContent,
  NavigationMenuTrigger,
  NavigationMenuLink,
  NavigationMenuIndicator,
  NavigationMenuViewport,
};
