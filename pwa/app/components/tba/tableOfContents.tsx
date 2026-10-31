import { useRouter, useRouterState } from '@tanstack/react-router';
import {
  createContext,
  startTransition,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { InView, type PlainChildrenProps } from 'react-intersection-observer';

import TableOfContentsIcon from '~icons/mdi/table-of-contents';

import { Button } from '~/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '~/components/ui/popover';
import {
  TableOfContentsItem,
  TableOfContentsLink,
  TableOfContentsList,
} from '~/components/ui/toc';

const TOCRendererContext = createContext<(content: React.ReactNode) => void>(
  () => {},
);

export function TOCRendererProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [content, setContent] = useState<React.ReactNode>(null);
  return (
    <TOCRendererContext.Provider value={setContent}>
      {/* Render the TOC header below navbar */}
      {/* The real bar is only set by an effect, so it is missing from the server HTML. The placeholder holds its space until then. */}
      {content ?? <TOCPlaceholder />}
      {/* Render the provider outlet children */}
      {children}
    </TOCRendererContext.Provider>
  );
}

export interface TocPreview {
  activeLabel: string;
  action?: React.ReactNode;
}

declare module '@tanstack/react-router' {
  interface StaticDataRouteOption {
    // The provider sits above the route, so it cannot see the route's
    // components during server rendering. A route that declares this gets its
    // label and action drawn in the placeholder, so the first paint matches
    // the real bar.
    tocPreview?: (loaderData: never) => TocPreview;
  }
}

function TOCPlaceholder() {
  const match = useRouterState({ select: (s) => s.matches.at(-1) });
  const tocPreview = match?.staticData.tocPreview as
    ((loaderData: unknown) => TocPreview) | undefined;
  const preview = tocPreview?.(match?.loaderData);

  return (
    <div
      data-toc-placeholder
      inert
      aria-hidden
      className="h-(--toc-bar-height) items-center justify-between gap-8
        border-b px-4"
    >
      {preview && (
        <>
          <div className="flex h-8 items-center gap-1.5 px-2 text-foreground">
            <TOCTriggerContent label={preview.activeLabel} />
          </div>
          {preview.action}
        </>
      )}
    </div>
  );
}

function firstLeafLabel(nodes: TocNode[]): string | undefined {
  let node = nodes[0];
  while (node?.children?.length) {
    node = node.children[0];
  }
  return node?.label;
}

function TOCTriggerContent({ label }: { label: string | undefined }) {
  return (
    <>
      <TableOfContentsIcon className="size-5" />
      <span className="text-sm">{label}</span>
    </>
  );
}

function TOCRenderPortal({ children }: { children: React.ReactNode }) {
  const setContent = useContext(TOCRendererContext);

  useEffect(() => {
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
      {/* Lets CSS show the placeholder only on pages that have a TOC (see tailwind.css). */}
      <span data-toc-marker hidden />
      {/* Desktop TOC - Split screen */}
      {!mobileOnly && (
        <div className="basis-full max-lg:hidden lg:basis-1/6">
          <div
            className="sticky top-[calc(var(--header-height)+0.5rem)] space-y-6"
          >
            {children}
            <TOCContent tocItems={tocItems} activeItem={activeItem} />
          </div>
        </div>
      )}
      {/* Mobile TOC - Sticky header */}
      <TOCRenderPortal>
        <div
          data-toc-bar
          className="sticky inset-x-0 top-(--header-height) z-1 flex
            h-(--toc-bar-height) items-center justify-between gap-8 border-b
            bg-background/80 px-4 text-muted-foreground backdrop-blur-xs
            transition-colors lg:hidden"
        >
          <div className="flex items-center gap-1">
            <Popover
              open={mobilePopoverOpen}
              onOpenChange={setMobilePopoverOpen}
            >
              <PopoverTrigger
                render={
                  <Button
                    variant="ghost"
                    className="h-8 gap-1.5 px-2 text-foreground"
                  />
                }
              >
                <TOCTriggerContent
                  // Falls back to the first section so the label matches the
                  // placeholder instead of going blank until the observer fires.
                  label={activeItem?.label ?? firstLeafLabel(tocItems)}
                />
              </PopoverTrigger>
              <PopoverContent
                side="top"
                align="start"
                sideOffset={0}
                className="max-h-[70vh] w-60 overflow-y-auto overscroll-contain
                  lg:hidden"
              >
                <TOCContent
                  tocItems={tocItems}
                  activeItem={activeItem}
                  onItemClick={() => setMobilePopoverOpen(false)}
                />
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
  className,
  ...props
}: TableOfContentsSectionProps) {
  return (
    <InView
      as="section"
      id={id}
      className={className}
      rootMargin="-15% 0px 0px 0px"
      onChange={(inView) => {
        // Low-priority update so pointer events/hover aren't blocked by the re-render
        startTransition(() => {
          setInView((prev) => {
            const next = new Set(prev);
            if (inView) {
              next.add(id);
            } else {
              next.delete(id);
            }
            return next;
          });
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
  onItemClick,
}: {
  tocItems: TocNode[];
  activeItem: TocNode | undefined;
  onItemClick?: () => void;
}) {
  return (
    <TableOfContentsList>
      {tocItems.map((node) => (
        <TOCNode
          key={node.slug}
          node={node}
          activeItem={activeItem}
          depth={0}
          onItemClick={onItemClick}
        />
      ))}
    </TableOfContentsList>
  );
}

function TOCNode({
  node,
  activeItem,
  depth,
  onItemClick,
}: {
  node: TocNode;
  activeItem: TocNode | undefined;
  depth: number;
  onItemClick?: () => void;
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

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLAnchorElement>) => {
      e.preventDefault();
      const element = document.getElementById(node.slug);
      if (element) {
        element.scrollIntoView({ behavior: 'instant', block: 'start' });
      }
      onItemClick?.();
    },
    [node.slug, onItemClick],
  );

  return (
    <>
      <TableOfContentsItem className="first:pt-0" indent={depth}>
        <TableOfContentsLink
          hash={node.slug}
          replace={true}
          isActive={isNodeOrDescendantActive}
          onClick={handleClick}
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
                onItemClick={onItemClick}
              />
            ))}
          </TableOfContentsList>
        </TableOfContentsItem>
      )}
    </>
  );
}
