import type { AnchorHTMLAttributes, ReactNode } from 'react';

type Params = Record<string, string | number | undefined>;

interface LinkProps extends Omit<
  AnchorHTMLAttributes<HTMLAnchorElement>,
  'href'
> {
  to?: string;
  params?: Params;
  search?: Record<string, string | number> | (() => unknown);
  hash?: string;
  activeProps?: unknown;
  activeOptions?: unknown;
  mask?: unknown;
  replace?: boolean;
  resetScroll?: boolean;
  preload?: unknown;
}

function buildHref({ to = '', params = {}, search, hash }: LinkProps) {
  const path = to
    // Optional segments like `/{-$year}` drop out when the param is undefined.
    .replace(/\/\{-\$(\w+)\}/g, (_, name: string) =>
      params[name] === undefined ? '' : `/${params[name]}`,
    )
    .replace(/\$(\w+)/g, (_, name: string) => String(params[name]));
  const query =
    search && typeof search === 'object'
      ? `?${new URLSearchParams(
          Object.entries(search).map(([k, v]) => [k, String(v)]),
        )}`
      : '';
  return `${path}${query}${hash ? `#${hash}` : ''}`;
}

export function Link({
  to,
  params,
  search,
  hash,
  activeProps: _activeProps,
  activeOptions: _activeOptions,
  mask: _mask,
  replace: _replace,
  resetScroll: _resetScroll,
  preload: _preload,
  children,
  ...props
}: LinkProps) {
  return (
    <a href={buildHref({ to, params, search, hash })} {...props}>
      {children}
    </a>
  );
}

export function ClientOnly({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
