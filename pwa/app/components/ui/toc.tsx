import { Link } from '@tanstack/react-router';
import * as React from 'react';

import { cn } from '~/lib/utils';

interface TableOfContentsListProps extends React.ComponentPropsWithoutRef<'ul'> {
  indent?: number;
}

const TableOfContentsList = React.forwardRef<
  React.ElementRef<'ul'>,
  TableOfContentsListProps
>(({ className, indent, ...props }, ref) => {
  const paddingClass = indent
    ? {
        1: 'pl-4',
        2: 'pl-8',
        3: 'pl-12',
        4: 'pl-16',
        5: 'pl-20',
      }[indent] || 'pl-24'
    : '';
  return (
    <ul
      ref={ref}
      className={cn('m-0 list-none', paddingClass, className)}
      {...props}
    />
  );
});
TableOfContentsList.displayName = 'TableOfContentsList';

const TableOfContentsTitle = React.forwardRef<
  React.ElementRef<'li'>,
  React.ComponentPropsWithoutRef<'li'>
>(({ className, ...props }, ref) => (
  <li
    ref={ref}
    className={cn('mb-2 text-sm font-medium', className)}
    {...props}
  />
));
TableOfContentsTitle.displayName = 'TableOfContentsTitle';

interface TableOfContentsItemProps extends React.ComponentPropsWithoutRef<'li'> {
  indent?: number;
}

const TableOfContentsItem = React.forwardRef<
  React.ElementRef<'li'>,
  TableOfContentsItemProps
>(({ className, indent, ...props }, ref) => {
  const marginClass = indent
    ? {
        1: 'ml-4',
        2: 'ml-8',
        3: 'ml-12',
        4: 'ml-16',
        5: 'ml-20',
      }[indent] || 'ml-24'
    : '';
  return (
    <li
      ref={ref}
      className={cn('mt-0 pt-2', marginClass, className)}
      {...props}
    />
  );
});
TableOfContentsItem.displayName = 'TableOfContentsItem';

interface TableOfContentsLinkProps extends React.ComponentPropsWithoutRef<
  typeof Link
> {
  isActive?: boolean;
}

const TableOfContentsLink = React.forwardRef<
  React.ElementRef<typeof Link>,
  TableOfContentsLinkProps
>(({ className, isActive, ...props }, ref) => (
  <Link
    ref={ref}
    className={cn(
      'text-sm font-medium text-foreground transition-colors hover:text-primary',
      isActive ? 'font-bold text-foreground' : 'text-muted-foreground',
      className,
    )}
    {...props}
  />
));
TableOfContentsLink.displayName = 'TableOfContentsLink';

export {
  TableOfContentsList,
  TableOfContentsTitle,
  TableOfContentsItem,
  TableOfContentsLink,
};
