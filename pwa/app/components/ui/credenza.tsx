import { type ComponentProps, createContext, useContext } from 'react';

import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '~/components/ui/dialog';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from '~/components/ui/drawer';
import { useMediaQuery } from '~/lib/hooks';
import { cn } from '~/lib/utils';

interface BaseProps {
  children: React.ReactNode;
}

interface RootCredenzaProps extends BaseProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface CredenzaProps extends BaseProps {
  className?: string;
  asChild?: true;
}

const desktop = '(min-width: 768px)';

// Computed once in Credenza and read by every sub-part, so Root and Content
// never disagree on Dialog vs Drawer mid-render (a mismatch mounts vaul's
// Drawer.Portal without its Drawer.Root context and crashes).
const CredenzaIsDesktopContext = createContext(false);

const Credenza = ({ children, ...props }: RootCredenzaProps) => {
  const isDesktop = useMediaQuery(desktop);
  const Credenza = isDesktop ? Dialog : Drawer;

  return (
    <CredenzaIsDesktopContext.Provider value={isDesktop}>
      <Credenza {...props} shouldScaleBackground={false}>
        {children}
      </Credenza>
    </CredenzaIsDesktopContext.Provider>
  );
};

const CredenzaTrigger = ({
  className,
  children,
  asChild,
  ...props
}: CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);

  if (isDesktop) {
    return (
      <DialogTrigger
        className={className}
        render={asChild ? (children as React.ReactElement) : undefined}
        {...props}
      >
        {asChild ? undefined : children}
      </DialogTrigger>
    );
  }

  return (
    <DrawerTrigger className={className} asChild={asChild} {...props}>
      {children}
    </DrawerTrigger>
  );
};

const CredenzaClose = ({
  className,
  children,
  asChild,
  ...props
}: CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);

  if (isDesktop) {
    return (
      <DialogClose
        className={className}
        render={asChild ? (children as React.ReactElement) : undefined}
        {...props}
      >
        {asChild ? undefined : children}
      </DialogClose>
    );
  }

  return (
    <DrawerClose className={className} asChild={asChild} {...props}>
      {children}
    </DrawerClose>
  );
};

const CredenzaContent = ({
  className,
  children,
  ...props
}: Omit<ComponentProps<typeof DialogContent>, 'className' | 'style'> &
  CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);
  const CredenzaContent = isDesktop ? DialogContent : DrawerContent;

  return (
    <CredenzaContent className={className} {...props}>
      {children}
    </CredenzaContent>
  );
};

const CredenzaDescription = ({
  className,
  children,
  ...props
}: CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);
  const CredenzaDescription = isDesktop ? DialogDescription : DrawerDescription;

  return (
    <CredenzaDescription className={className} {...props}>
      {children}
    </CredenzaDescription>
  );
};

const CredenzaHeader = ({ className, children, ...props }: CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);
  const CredenzaHeader = isDesktop ? DialogHeader : DrawerHeader;

  return (
    <CredenzaHeader className={className} {...props}>
      {children}
    </CredenzaHeader>
  );
};

const CredenzaTitle = ({ className, children, ...props }: CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);
  const CredenzaTitle = isDesktop ? DialogTitle : DrawerTitle;

  return (
    <CredenzaTitle className={className} {...props}>
      {children}
    </CredenzaTitle>
  );
};

const CredenzaBody = ({ className, children, ...props }: CredenzaProps) => {
  return (
    <div className={cn('px-4 md:px-0', className)} {...props}>
      {children}
    </div>
  );
};

const CredenzaFooter = ({ className, children, ...props }: CredenzaProps) => {
  const isDesktop = useContext(CredenzaIsDesktopContext);
  const CredenzaFooter = isDesktop ? DialogFooter : DrawerFooter;

  return (
    <CredenzaFooter className={className} {...props}>
      {children}
    </CredenzaFooter>
  );
};

export {
  Credenza,
  CredenzaBody,
  CredenzaClose,
  CredenzaContent,
  CredenzaDescription,
  CredenzaFooter,
  CredenzaHeader,
  CredenzaTitle,
  CredenzaTrigger,
};
