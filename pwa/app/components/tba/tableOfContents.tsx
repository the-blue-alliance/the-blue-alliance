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
  useMemo,
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
export interface TocNode {
  /** The hash/id to scroll to when clicked */
  slug: string;
  /** The display text for this node */
  label: string;
  /** Child nodes - supports arbitrary nesting levels */
  children?: TocNode[];
}

export function TableOfContents({
  children,
  tocItems,
  inView,
  mobileOnly = false,
}: {
  children?: React.ReactNode;
  tocItems: TocNode[];
  inView: Set<string>;
  mobileOnly?: boolean;
}) {
  const [mobilePopoverOpen, setMobilePopoverOpen] = useState<boolean>(false);
  const router = useRouter();

  const activeItem = useMemo(() => {
    const findAllLeafNodes = (nodes: TocNode[]): TocNode[] => {
      const leafNodes: TocNode[] = [];
      for (const node of nodes) {
        if (node.slug) {
          leafNodes.push(node);
        }
        if (node.children) {
          leafNodes.push(...findAllLeafNodes(node.children));
        }
      }
      return leafNodes;
    };

    const allItems = findAllLeafNodes(tocItems);
    return allItems.find((item) => item.slug && inView.has(item.slug));
  }, [tocItems, inView]);

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
      {!mobileOnly && (
        <div className="basis-full max-lg:hidden lg:basis-1/6">
          <div className="sticky top-14 space-y-6 pt-8">
            {children}
            <TOCContent tocItems={tocItems} activeItem={activeItem} />
          </div>
        </div>
      )}
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
                  variant="ghost"
                  className="h-8 gap-1.5 px-2 text-foreground"
                >
                  <TableOfContentsIcon className="size-5" />
                  <span className="text-sm">{activeItem?.label}</span>
                </Button>
              </PopoverTrigger>
              <PopoverContent
                side="top"
                align="start"
                sideOffset={0}
                className="max-h-[70vh] w-60 overflow-y-auto lg:hidden"
              >
                <TOCContent tocItems={tocItems} activeItem={activeItem} />
              </PopoverContent>
            </Popover>
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
      className="scroll-mt-12 lg:scroll-mt-4"
      rootMargin="-15% 0px 0px 0px"
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
  activeItem,
}: {
  tocItems: TocNode[];
  activeItem: TocNode | undefined;
}) {
  return (
    <TableOfContentsList>
      {tocItems.map((node) => (
        <TOCNode
          key={node.slug}
          node={node}
          activeItem={activeItem}
          depth={0}
        />
      ))}
    </TableOfContentsList>
  );
}

function TOCNode({
  node,
  activeItem,
  depth,
}: {
  node: TocNode;
  activeItem: TocNode | undefined;
  depth: number;
}) {
  // Check if this node or any of its descendants is active
  const isNodeOrDescendantActive = useMemo(() => {
    const checkActive = (n: TocNode): boolean => {
      if (n.slug === activeItem?.slug) {
        return true;
      }
      if (n.children) {
        return n.children.some(checkActive);
      }
      return false;
    };
    return checkActive(node);
  }, [node, activeItem]);

  return (
    <>
      <TableOfContentsItem className="first:pt-0" indent={depth}>
        <TableOfContentsLink
          hash={node.slug}
          replace={true}
          isActive={isNodeOrDescendantActive}
        >
          {node.label}
        </TableOfContentsLink>
      </TableOfContentsItem>
      {node.children && (
        <TableOfContentsItem>
          <TableOfContentsList>
            {node.children.map((child) => (
              <TOCNode
                key={child.slug}
                node={child}
                activeItem={activeItem}
                depth={depth + 1}
              />
            ))}
          </TableOfContentsList>
        </TableOfContentsItem>
      )}
    </>
  );
}
