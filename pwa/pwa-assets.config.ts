import {
  AllAppleDeviceNames,
  Preset,
  createAppleSplashScreens,
  defineConfig,
} from '@vite-pwa/assets-generator/config';

export const preset: Preset = {
  transparent: {
    sizes: [],
    favicons: [],
  },
  maskable: {
    sizes: [],
  },
  apple: {
    sizes: [],
  },
  appleSplashScreens: createAppleSplashScreens(
    {
      padding: 0.8,
      resizeOptions: { background: '#3F51B5', fit: 'contain' },
      linkMediaOptions: {
        log: true,
        addMediaScreen: true,
        basePath: '/icons/',
        xhtml: true,
      },
      png: {
        compressionLevel: 9,
        quality: 60,
      },
      name: (landscape, size) => {
        return `apple-splash-${landscape ? 'landscape' : 'portrait'}-${size.width}x${size.height}.png`;
      },
    },
    AllAppleDeviceNames,
  ),
};

export default defineConfig({
  headLinkOptions: {
    preset: '2023',
  },
  preset,
  images: ['public/icons/tba-lamp.svg'],
});
