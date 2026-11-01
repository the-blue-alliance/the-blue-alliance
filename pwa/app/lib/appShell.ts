import { useHydrated, useRouter } from '@tanstack/react-router';

/**
 * Repeat visits load the app shell instead of a server-rendered page: the
 * service worker answers every page load with `/_shell.html`, which holds the
 * root layout prerendered at `/` and no route data (see `spa` in
 * vite.config.ts and scripts/generate-sw.ts). The router then loads the page
 * in the browser.
 *
 * The root route marks the shell with this attribute on `<html>`.
 */
export const APP_SHELL_ATTRIBUTE = 'data-app-shell';

/** Whether this document came from the app shell rather than SSR. */
export function isAppShellDocument(): boolean {
  return document.documentElement.hasAttribute(APP_SHELL_ATTRIBUTE);
}

/**
 * True while rendering the app shell's markup: when prerendering it, and while
 * React hydrates it. The shell's root layout was rendered at `/`, and React
 * keeps mismatched attributes when it hydrates, so parts of the layout that
 * depend on the URL (active links, for example) should be keyed on this to
 * remount once hydration is done.
 */
export function useIsHydratingAppShell(): boolean {
  const router = useRouter();
  const hydrated = useHydrated();
  if (router.isServer) {
    return router.isShell();
  }
  return !hydrated && isAppShellDocument();
}
