import { Button } from 'app/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from 'app/components/ui/popover';
import {
  TableOfContentsItem,
  TableOfContentsLink,
  TableOfContentsList,
} from 'app/components/ui/toc';
import { InView, type PlainChildrenProps } from 'react-intersection-observer';

import IconTOC from '~icons/mdi/table-of-contents';

function TOCContent({
  tocItems,
  inView,
}: {
  tocItems: { slug: string; label: string }[];
  inView: Set<string>;
}) {
  const firstInViewItem = tocItems.find((item) => inView.has(item.slug));
  return (
    <TableOfContentsList>
      {tocItems.map((item) => (
        <TableOfContentsItem key={item.slug} className="first:pt-0">
          <TableOfContentsLink
            to={`#${item.slug}`}
            replace={true}
            isActive={item.slug === firstInViewItem?.slug}
          >
            {item.label}
          </TableOfContentsLink>
        </TableOfContentsItem>
      ))}
    </TableOfContentsList>
  );
}

export function TableOfContentsPopover({
  children,
  tocItems,
  inView,
}: {
  children?: React.ReactNode;
  tocItems: { slug: string; label: string }[];
  inView: Set<string>;
}) {
  return (
    <>
      <div className="hidden basis-full lg:block lg:basis-1/6">
        <div className="sticky top-14 pt-8">
          {children}
          <TOCContent tocItems={tocItems} inView={inView} />
        </div>
      </div>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            className="fixed right-4 bottom-4 z-40 flex size-14 items-center
              justify-center rounded-full shadow-sm lg:hidden"
            aria-label="Table of Contents"
          >
            <IconTOC className="size-6" />
          </Button>
        </PopoverTrigger>
        <PopoverContent
          side="top"
          align="end"
          sideOffset={12}
          className="max-h-[70vh] w-60 overflow-y-auto lg:hidden"
        >
          <div className="space-y-3">
            {children}
            <TOCContent tocItems={tocItems} inView={inView} />
          </div>
        </PopoverContent>
      </Popover>
    </>
  );
}

type TableOfContentsSectionProps = Omit<
  PlainChildrenProps,
  'onChange' | 'ref'
> & {
  children: React.ReactNode;
  id: string;
  setInView: React.Dispatch<React.SetStateAction<Set<string>>>;
};

export function TableOfContentsSection({
  children,
  id,
  setInView,
  ...props
}: TableOfContentsSectionProps) {
  return (
    <InView
      as="section"
      id={id}
      onChange={(inView) => {
        setInView((prev) => {
          if (inView) {
            prev.add(id);
          } else {
            prev.delete(id);
          }
          return new Set(prev);
        });
      }}
      {...props}
    >
      {children}
    </InView>
  );
}
