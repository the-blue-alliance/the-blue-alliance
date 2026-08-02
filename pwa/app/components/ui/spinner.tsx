import Loader2Icon from '~icons/lucide/loader-2';

import { cn } from '~/lib/utils';

function Spinner({ className, ...props }: React.ComponentProps<'svg'>) {
  return (
    <Loader2Icon
      // The suggested `<output>` tag isn't an option here: this renders an
      // <svg>, which can't carry the role implicitly.
      // eslint-disable-next-line jsx-a11y/prefer-tag-over-role
      role="status"
      aria-label="Loading"
      className={cn('size-4 animate-spin', className)}
      {...props}
    />
  );
}

export { Spinner };
