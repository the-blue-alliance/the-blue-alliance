import { Toaster as Sonner } from 'sonner';

import CircleCheckIcon from '~icons/lucide/circle-check';
import InfoIcon from '~icons/lucide/info';
import LoaderCircleIcon from '~icons/lucide/loader-circle';
import OctagonXIcon from '~icons/lucide/octagon-x';
import TriangleAlertIcon from '~icons/lucide/triangle-alert';

import { useTheme } from '~/lib/theme';

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = 'system' } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps['theme']}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="h-4 w-4" />,
        info: <InfoIcon className="h-4 w-4" />,
        warning: <TriangleAlertIcon className="h-4 w-4" />,
        error: <OctagonXIcon className="h-4 w-4" />,
        loading: <LoaderCircleIcon className="h-4 w-4 animate-spin" />,
      }}
      toastOptions={{
        classNames: {
          toast:
            'group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg',
          success: 'group-[.toaster]:!border-green-500',
          error: 'group-[.toaster]:!border-red-500',
          description: 'group-[.toast]:text-muted-foreground',
          actionButton:
            'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground',
          cancelButton:
            'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground',
        },
      }}
      {...props}
    />
  );
};

export { Toaster };
