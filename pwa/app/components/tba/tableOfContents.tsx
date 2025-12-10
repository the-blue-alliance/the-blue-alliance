import { useRouter } from '@tanstack/react-router';
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
import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
} from 'react';
import { InView, type PlainChildrenProps } from 'react-intersection-observer';

import TableOfContentsIcon from '~icons/mdi/table-of-contents';

const TOCRendererContext = createContext<{
  content: React.ReactNode;
  setContent: (content: React.ReactNode) => void;
}>({
  content: null,
  setContent: () => {},
});

export function TOCRendererProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [content, setContent] = useState<React.ReactNode>(null);
  return (
    <TOCRendererContext.Provider value={{ content, setContent }}>
      {/* Render the TOC header below navbar */}
      {content}
      {/* Render the provider outlet children */}
      {children}
    </TOCRendererContext.Provider>
  );
}

function TOCRenderPortal({ children }: { children: React.ReactNode }) {
  const { setContent } = useContext(TOCRendererContext);

  useLayoutEffect(() => {
    setContent(children);
  }, [children, setContent]);

  // Clear the content on unmount
  useEffect(() => {
    return () => {
      setContent(null);
    };
  }, [setContent]);

  return null;
}

export function TableOfContents({
  children,
  tocItems,
  inView,
}: {
  children?: React.ReactNode;
  tocItems: { slug: string; label: string }[];
  inView: Set<string>;
}) {
  const [mobilePopoverOpen, setMobilePopoverOpen] = useState<boolean>(false);
  const router = useRouter();

  const firstInViewItem = tocItems.find((item) => inView.has(item.slug));

  // Close mobile TOC on click
  useEffect(() => {
    const unsubscribe = router.subscribe('onBeforeNavigate', () => {
      setMobilePopoverOpen(false);
    });
    return () => unsubscribe();
  }, [router, setMobilePopoverOpen]);

  return (
    <>
      {/* Desktop TOC - Split screen */}
      <div className="basis-full max-lg:hidden lg:basis-1/6">
        <div className="sticky top-14 space-y-6 pt-8">
          {children}
          <TOCContent tocItems={tocItems} inView={inView} />
        </div>
      </div>
      {/* Mobile TOC - Sticky header */}
      <TOCRenderPortal>
        <div
          className="sticky inset-x-0 top-14 z-1 flex items-center
            justify-between gap-8 border-b bg-background/80 px-4 py-1
            text-muted-foreground backdrop-blur-xs transition-colors lg:hidden"
        >
          <div className="flex items-center gap-1">
            <Popover
              open={mobilePopoverOpen}
              onOpenChange={setMobilePopoverOpen}
            >
              <PopoverTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  className="size-8 text-foreground"
                >
                  <TableOfContentsIcon className="size-5" />
                </Button>
              </PopoverTrigger>
              <PopoverContent
                side="top"
                align="start"
                sideOffset={0}
                className="max-h-[70vh] w-60 overflow-y-auto lg:hidden"
              >
                <TOCContent tocItems={tocItems} inView={inView} />
              </PopoverContent>
            </Popover>
            <span className="text-sm">{firstInViewItem?.label}</span>
          </div>
          {children}
        </div>
      </TOCRenderPortal>
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
            hash={item.slug}
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
