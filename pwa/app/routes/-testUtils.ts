// Shared helpers for the route-module unit tests beside this file. The `-`
// prefix keeps TanStack's route generator from treating it as a route.

type Fn = (...args: never[]) => unknown;

type OptionResult<R, K extends string> = R extends {
  options: { [P in K]?: infer F };
}
  ? Awaited<ReturnType<Extract<F, Fn>>>
  : never;

/** Calls a route's `loader` option with a hand-built loader context. */
export function runLoader<R extends { options: object }>(
  route: R,
  context: object,
): Promise<OptionResult<R, 'loader'>> {
  const { loader } = route.options as { loader: (ctx: object) => unknown };
  return Promise.resolve(loader(context)) as Promise<OptionResult<R, 'loader'>>;
}

/** Calls a route's synchronous `head` option. */
export function runHead<R extends { options: object }>(
  route: R,
  context: object = {},
): OptionResult<R, 'head'> {
  const { head } = route.options as { head: (ctx: object) => unknown };
  return head(context) as OptionResult<R, 'head'>;
}

/** Runs raw search params through a route's zod `validateSearch` schema. */
export function runValidateSearch(
  route: { options: object },
  search: Record<string, unknown>,
): unknown {
  const { validateSearch } = route.options as {
    validateSearch: { parse: (input: unknown) => unknown };
  };
  return validateSearch.parse(search);
}
