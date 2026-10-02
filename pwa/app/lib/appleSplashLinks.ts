interface AppleSplashLink {
  rel: 'apple-touch-startup-image';
  media: string;
  href: string;
}

interface SplashImageProfile {
  deviceWidth: number;
  deviceHeight: number;
  pixelRatio: number;
  portraitAsset: string;
  landscapeAsset: string;
}

const APPLE_SPLASH_IMAGES = import.meta.glob<string>(
  '../images/apple-splash/apple-splash-*.png',
  {
    eager: true,
    import: 'default',
    query: '?url&no-inline',
  },
);

const SPLASH_IMAGE_PROFILES: SplashImageProfile[] = [
  {
    deviceWidth: 1024,
    deviceHeight: 1366,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-2048x2732.png',
    landscapeAsset: 'apple-splash-landscape-2732x2048.png',
  },
  {
    deviceWidth: 834,
    deviceHeight: 1194,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-1668x2388.png',
    landscapeAsset: 'apple-splash-landscape-2388x1668.png',
  },
  {
    deviceWidth: 768,
    deviceHeight: 1024,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-1536x2048.png',
    landscapeAsset: 'apple-splash-landscape-2048x1536.png',
  },
  {
    deviceWidth: 834,
    deviceHeight: 1112,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-1668x2224.png',
    landscapeAsset: 'apple-splash-landscape-2224x1668.png',
  },
  {
    deviceWidth: 810,
    deviceHeight: 1080,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-1620x2160.png',
    landscapeAsset: 'apple-splash-landscape-2160x1620.png',
  },
  {
    deviceWidth: 430,
    deviceHeight: 932,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1290x2796.png',
    landscapeAsset: 'apple-splash-landscape-2796x1290.png',
  },
  {
    deviceWidth: 393,
    deviceHeight: 852,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1179x2556.png',
    landscapeAsset: 'apple-splash-landscape-2556x1179.png',
  },
  {
    deviceWidth: 428,
    deviceHeight: 926,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1284x2778.png',
    landscapeAsset: 'apple-splash-landscape-2778x1284.png',
  },
  {
    deviceWidth: 390,
    deviceHeight: 844,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1170x2532.png',
    landscapeAsset: 'apple-splash-landscape-2532x1170.png',
  },
  {
    deviceWidth: 375,
    deviceHeight: 812,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1125x2436.png',
    landscapeAsset: 'apple-splash-landscape-2436x1125.png',
  },
  {
    deviceWidth: 414,
    deviceHeight: 896,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1242x2688.png',
    landscapeAsset: 'apple-splash-landscape-2688x1242.png',
  },
  {
    deviceWidth: 414,
    deviceHeight: 896,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-828x1792.png',
    landscapeAsset: 'apple-splash-landscape-1792x828.png',
  },
  {
    deviceWidth: 414,
    deviceHeight: 736,
    pixelRatio: 3,
    portraitAsset: 'apple-splash-portrait-1242x2208.png',
    landscapeAsset: 'apple-splash-landscape-2208x1242.png',
  },
  {
    deviceWidth: 375,
    deviceHeight: 667,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-750x1334.png',
    landscapeAsset: 'apple-splash-landscape-1334x750.png',
  },
  {
    deviceWidth: 320,
    deviceHeight: 568,
    pixelRatio: 2,
    portraitAsset: 'apple-splash-portrait-640x1136.png',
    landscapeAsset: 'apple-splash-landscape-1136x640.png',
  },
];

function buildMediaQuery(profile: SplashImageProfile, orientation: string) {
  return (
    `screen and (device-width: ${profile.deviceWidth}px) ` +
    `and (device-height: ${profile.deviceHeight}px) ` +
    `and (-webkit-device-pixel-ratio: ${profile.pixelRatio}) ` +
    `and (orientation: ${orientation})`
  );
}

function getSplashImageUrl(fileName: string) {
  const imageUrl = APPLE_SPLASH_IMAGES[`../images/apple-splash/${fileName}`];
  if (!imageUrl) throw new Error(`Missing Apple splash image: ${fileName}`);
  return imageUrl;
}

export const APPLE_SPLASH_STARTUP_LINKS: AppleSplashLink[] =
  SPLASH_IMAGE_PROFILES.flatMap((profile) => [
    {
      rel: 'apple-touch-startup-image',
      media: buildMediaQuery(profile, 'portrait'),
      href: getSplashImageUrl(profile.portraitAsset),
    },
    {
      rel: 'apple-touch-startup-image',
      media: buildMediaQuery(profile, 'landscape'),
      href: getSplashImageUrl(profile.landscapeAsset),
    },
  ]);
