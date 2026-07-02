import { describe, expect, test } from 'vitest';

import { APPLE_SPLASH_STARTUP_LINKS } from '~/lib/appleSplashLinks';

describe.concurrent('APPLE_SPLASH_STARTUP_LINKS', () => {
  test('contains one link per startup image variant', () => {
    expect(APPLE_SPLASH_STARTUP_LINKS).toHaveLength(30);
    expect(
      APPLE_SPLASH_STARTUP_LINKS.every(
        (link) =>
          link.rel === 'apple-touch-startup-image' &&
          typeof link.media === 'string' &&
          typeof link.href === 'string' &&
          link.media.length > 0 &&
          link.href.length > 0,
      ),
    ).toEqual(true);
  });

  test('includes both portrait and landscape for each device profile', () => {
    const mediaByDeviceProfile = new Map<string, Set<string>>();

    for (const link of APPLE_SPLASH_STARTUP_LINKS) {
      const orientation = link.media.includes('(orientation: portrait)')
        ? 'portrait'
        : 'landscape';
      const profile = link.media
        .replace(' and (orientation: portrait)', '')
        .replace(' and (orientation: landscape)', '');
      if (!mediaByDeviceProfile.has(profile))
        mediaByDeviceProfile.set(profile, new Set());
      mediaByDeviceProfile.get(profile)?.add(orientation);
    }

    expect(mediaByDeviceProfile.size).toEqual(15);
    expect(
      [...mediaByDeviceProfile.values()].every(
        (orientations) =>
          orientations.has('portrait') && orientations.has('landscape'),
      ),
    ).toEqual(true);
  });
});
