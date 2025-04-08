import * as React from 'react';
import { Link } from 'react-router';

import { cn } from '~/lib/utils';

interface TableOfContentsListProps
  extends React.ComponentPropsWithoutRef<'ul'> {
  indent?: boolean;
}

interface TableOfContentsItemProps
  extends React.ComponentPropsWithoutRef<'li'> {
  indent?: boolean;
}

interface TableOfContentsLinkProps
  extends React.ComponentPropsWithoutRef<typeof Link> {
  isActive?: boolean;
}

function TableOfContentsList({
  className,
  indent,
  ...props
}: TableOfContentsListProps) {
  return (
    <ul
      className={cn('m-0 list-none', indent && 'pl-4', className)}
      {...props}
    />
  );
}

function TableOfContentsTitle({
  className,
  ...props
}: React.ComponentPropsWithoutRef<'li'>) {
  return (
    <li className={cn('mb-2 text-sm font-medium', className)} {...props} />
  );
}

function TableOfContentsItem({
  className,
  indent,
  ...props
}: TableOfContentsItemProps) {
  return (
    <li className={cn('mt-0 pt-2', indent && 'ml-4', className)} {...props} />
  );
}

function TableOfContentsLink({
  className,
  isActive,
  ...props
}: TableOfContentsLinkProps) {
  return (
    <Link
      className={cn(
        'text-sm font-medium text-foreground transition-colors hover:text-primary',
        isActive ? 'font-medium text-foreground' : 'text-muted-foreground',
        className,
      )}
      {...props}
    />
  );
}

export {
  TableOfContentsList,
  TableOfContentsTitle,
  TableOfContentsItem,
  TableOfContentsLink,
};
