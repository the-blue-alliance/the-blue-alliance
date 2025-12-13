import { type VariantProps, cva } from 'class-variance-authority';
import React from 'react';

import MdiArrowLeft from '~icons/mdi/arrow-left';
import MdiArrowRight from '~icons/mdi/arrow-right';

import { Table, TableBody, TableCell, TableRow } from '~/components/ui/table';
import { cn } from '~/lib/utils';

export function ScoreBreakdownTable({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Table
      className={cn(
        'table-fixed overflow-hidden rounded-lg text-center',
        className,
      )}
    >
      <colgroup>
        <col />
        <col className="w-[45%]" />
        <col />
      </colgroup>
      <TableBody className="">{children}</TableBody>
    </Table>
  );
}

export function ScoreBreakdownRow({
  children,
  blueValue = undefined,
  redValue = undefined,
}: {
  children: React.ReactNode;
  blueValue?: number;
  redValue?: number;
}) {
  const redWon = (redValue ?? 0) > (blueValue ?? 0);
  const blueWon = (blueValue ?? 0) > (redValue ?? 0);

  return (
    <TableRow
      className={cn({
        // For some reason just first:font-bold applies to the entire row
        // so we need this kinda verbose hack
        '[&>*:first-child]:font-bold [&>*:last-child]:font-normal': redWon,
        '[&>*:first-child]:font-normal [&>*:last-child]:font-bold': blueWon,
      })}
    >
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(
            child as React.ReactElement<{
              redWon?: boolean;
              blueWon?: boolean;
            }>,
            {
              redWon,
              blueWon,
            },
          );
        }
        return child;
      })}
    </TableRow>
  );
}

const cellVariants = cva('', {
  variants: {
    color: {
      red: '',
      blue: '',
      neutral: '',
    },
    shade: {
      light: '',
      dark: '',
    },
    fontWeight: {
      normal: '',
      bold: 'font-bold',
    },
  },
  compoundVariants: [
    {
      color: 'red',
      shade: 'light',
      class: 'bg-alliance-red/15',
    },
    {
      color: 'red',
      shade: 'dark',
      class: 'bg-alliance-red/20',
    },
    {
      color: 'blue',
      shade: 'light',
      class: 'bg-alliance-blue/15',
    },
    {
      color: 'blue',
      shade: 'dark',
      class: 'bg-alliance-blue/20',
    },
    {
      color: 'neutral',
      shade: 'light',
      class: 'bg-gray-50',
    },
    {
      color: 'neutral',
      shade: 'dark',
      class: 'bg-gray-200',
    },
  ],
  defaultVariants: {
    color: 'neutral',
    shade: 'light',
    fontWeight: 'normal',
  },
});

interface ScoreBreakdownCellProps
  extends
    React.ComponentPropsWithoutRef<typeof TableCell>,
    Omit<VariantProps<typeof cellVariants>, 'color'> {
  color: 'red' | 'blue' | 'neutral';
  children?: React.ReactNode;
}

export function ScoreBreakdownAllianceCell({
  color,
  shade,
  fontWeight,
  className,
  children,
  ...props
}: ScoreBreakdownCellProps) {
  return (
    <TableCell
      className={cn(cellVariants({ color, shade, fontWeight }), className)}
      {...props}
    >
      {children}
    </TableCell>
  );
}

export function ScoreBreakdownLabelCell({
  shade,
  fontWeight,
  className,
  children,
  redWon,
  blueWon,
  ...props
}: Omit<ScoreBreakdownCellProps, 'color'> & {
  redWon?: boolean;
  blueWon?: boolean;
}) {
  return (
    <TableCell
      className={cn(
        cellVariants({ color: 'neutral', shade, fontWeight }),
        className,
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div className="flex w-6 items-center justify-center">
          {redWon && <MdiArrowLeft />}
        </div>
        <div className="w-[80%] text-center">{children}</div>
        <div className="flex w-6 items-center justify-center">
          {blueWon && <MdiArrowRight />}
        </div>
      </div>
    </TableCell>
  );
}

ScoreBreakdownLabelCell.displayName = 'ScoreBreakdownLabelCell';
