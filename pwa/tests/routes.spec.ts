import { expect, test } from '@playwright/test';

import type { FileRouteTypes } from '~/routeTree.gen';

type RoutePath = FileRouteTypes['fullPaths'];

// Keep the runtime route list in sync with TanStack Router's generated route
// types. A newly added or removed route must be reflected here before its
// smoke test can be generated.
function defineAllRoutes<T extends readonly RoutePath[]>(
  routes: T &
    ([RoutePath] extends [T[number]] ? unknown : 'Missing routes') &
    ([T[number]] extends [RoutePath] ? unknown : 'Extra routes'),
): T {
  return routes;
}

const allRoutes = defineAllRoutes([
  '/',
  '/about',
  '/account/',
  '/account/mytba',
  '/add-data',
  '/apidocs',
  '/apidocs/v3',
  '/contact',
  '/district/$districtAbbreviation/{-$year}',
  '/district/$districtAbbreviation/insights',
  '/district/$districtAbbreviation/stats',
  '/district/$districtAbbreviation/champs/$year',
  '/districts/{-$year}',
  '/donate',
  '/event/$eventKey',
  '/events/$districtAbbreviation/$year',
  '/events/{-$year}',
  '/gameday',
  '/gameday/$eventCode',
  '/hall-of-fame',
  '/insights/{-$year}',
  '/local/debug',
  '/match_suggestion',
  '/match/$matchKey',
  '/privacy',
  '/search',
  '/suggest/review/',
  '/suggest/review/$suggestionType',
  '/suggest/team/media',
  '/team/$teamNumber/{-$year}',
  '/team/$teamNumber/history',
  '/team/$teamNumber/stats',
  '/teams/{-$pgNum}',
  '/thanks',
  '/webcasts',
] as const);

type RouteParameterToken<Segment extends string> =
  Segment extends `{-$${infer Parameter}}`
    ? `{-$${Parameter}}`
    : Segment extends `$${infer Parameter}`
      ? `$${Parameter}`
      : never;

type RouteParameters<Path extends string> =
  Path extends `${infer Segment}/${infer Rest}`
    ? RouteParameterToken<Segment> | RouteParameters<Rest>
    : RouteParameterToken<Path>;

type RouteParameter = RouteParameters<(typeof allRoutes)[number]>;

const parameterValues = {
  $eventKey: ['2024mil'],
  $eventCode: ['2024mil'],
  '{-$year}': ['', '2024'],
  $matchKey: ['2024mil_f1m2'],
  $year: ['2024'],
  '{-$pgNum}': ['', '1'],
  $districtAbbreviation: ['fim'],
  $teamNumber: ['604'],
  $suggestionType: ['match'],
} satisfies Record<RouteParameter, readonly string[]>;

interface RouteTestCase {
  path: string;
}

function cartesianProduct<T>(arrays: readonly (readonly T[])[]): T[][] {
  return arrays.reduce<T[][]>(
    (products, values) =>
      products.flatMap((product) => values.map((value) => [...product, value])),
    [[]],
  );
}

function getRouteParameters(route: RoutePath): RouteParameter[] {
  return (route.match(/(\$\w+|\{-\$\w+\})/g) ?? []) as RouteParameter[];
}

function generateRouteTestCases(): RouteTestCase[] {
  return allRoutes.flatMap((route) => {
    const parameters = getRouteParameters(route);
    const combinations = cartesianProduct(
      parameters.map((parameter) => parameterValues[parameter]),
    );

    return combinations.map((combination) => ({
      path: parameters.reduce<string>(
        (path, parameter, index) =>
          path.replace(parameter, combination[index] ?? ''),
        route,
      ),
    }));
  });
}

const routeTestCases = generateRouteTestCases();

test.describe('Route smoke tests', () => {
  for (const { path } of routeTestCases) {
    test(`${path} reaches hydrated state without runtime errors`, async ({
      page,
    }) => {
      const pageErrors: Error[] = [];
      page.on('pageerror', (error) => pageErrors.push(error));

      await page.goto(path);
      await expect(page.locator('body[data-hydrated]')).toBeVisible();

      expect(pageErrors).toHaveLength(0);
    });
  }
});
