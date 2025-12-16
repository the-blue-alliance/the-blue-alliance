import { expect, test } from '@playwright/test';

import type { FileRouteTypes } from '~/routeTree.gen';

// Extract all route paths from the generated route tree types
type RoutePath = FileRouteTypes['fullPaths'];

// Type-safe helper that ensures all routes are included
// This will cause a compile error if any route is missing or extra
function defineAllRoutes<T extends readonly RoutePath[]>(
  routes: T &
    ([RoutePath] extends [T[number]] ? unknown : 'Missing routes') &
    ([T[number]] extends [RoutePath] ? unknown : 'Extra routes'),
): T {
  return routes;
}

// All routes are automatically extracted from the type system
// TypeScript will error if this list is incomplete or contains invalid routes
const allRoutes = defineAllRoutes([
  '/',
  '/about',
  '/account',
  '/account/mytba',
  '/add-data',
  '/apidocs',
  '/apidocs/v3',
  '/contact',
  '/district/$districtAbbreviation/{-$year}',
  '/district/$districtAbbreviation/insights',
  '/donate',
  '/event/$eventKey',
  '/events/{-$year}',
  '/gameday',
  '/insights/{-$year}',
  '/local/debug',
  '/match_suggestion',
  '/match/$matchKey',
  '/privacy',
  '/team/$teamNumber/{-$year}',
  '/team/$teamNumber/history',
  '/team/$teamNumber/stats',
  '/teams/{-$pgNum}',
  '/thanks',
] as const);

// Define test data for dynamic route parameters
// Only need to specify values for parameters, not list out every route manually
const parameterValues: Record<string, string[]> = {
  $eventKey: ['2024mil'],
  '{-$year}': ['', '2024'],
  $matchKey: ['2024mil_f1m2'],
  '{-$pgNum}': ['', '1'],
  $districtAbbreviation: ['fim'],
  $teamNumber: ['604'],
};

/**
 * Generates the cartesian product of arrays
 * @example cartesianProduct([['a', 'b'], ['1', '2']]) => [['a', '1'], ['a', '2'], ['b', '1'], ['b', '2']]
 */
function cartesianProduct<T>(arrays: T[][]): T[][] {
  if (arrays.length === 0) return [[]];
  if (arrays.length === 1) return arrays[0].map((item) => [item]);

  const [first, ...rest] = arrays;
  const restProduct = cartesianProduct(rest);

  return first.flatMap((item) => restProduct.map((prod) => [item, ...prod]));
}

function generateTestCases(): string[] {
  const testCases: string[] = [];

  for (const route of allRoutes) {
    // Find all parameter placeholders in the route
    const paramMatches = route.match(/(\$\w+|\{-\$\w+\})/g);

    if (!paramMatches) {
      // Static route: add as-is
      testCases.push(route);
    } else {
      // Dynamic route: generate test cases for all parameter combinations
      // Get all possible values for each parameter
      const paramValueArrays = paramMatches.map(
        (param) => parameterValues[param],
      );

      // Generate cartesian product of all parameter combinations
      const combinations = cartesianProduct(paramValueArrays);

      // For each combination, replace parameters in the route
      for (const combination of combinations) {
        let testPath: string = route;
        for (let i = 0; i < paramMatches.length; i++) {
          testPath = testPath.replace(paramMatches[i], combination[i]);
        }
        testCases.push(testPath);
      }
    }
  }
  return testCases;
}

const routeTestCases = generateTestCases();

test.describe('Route smoke tests', () => {
  for (const testCase of routeTestCases) {
    test(`${testCase} renders without errors`, async ({ page }) => {
      const errors: string[] = [];
      page.on('pageerror', (exception) => {
        errors.push(exception.message);
      });

      await page.goto(testCase);

      // Verify no page errors occurred
      expect(errors).toHaveLength(0);

      // Verify page loaded (body is visible)
      await expect(page.locator('body')).toBeVisible();
    });
  }
});
