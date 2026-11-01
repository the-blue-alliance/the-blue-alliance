/**
 * Path prefixes that change the root layout. The app shell is prerendered with
 * the default layout, so the service worker sends page loads for these to the
 * server instead (see scripts/generate-sw.ts).
 */

/** Rendered without the navbar, footer, or page container. */
export const FULLSCREEN_ROUTES = ['/gameday'];

/** Rendered without the page container's width limit. */
export const FULLWIDTH_ROUTES = ['/match_suggestion'];
