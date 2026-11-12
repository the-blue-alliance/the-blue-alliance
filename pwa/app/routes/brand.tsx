import { createFileRoute } from '@tanstack/react-router';

import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/brand')({
  headers: publicCacheControlHeaders(),
  component: Brand,
  head: () => {
    return {
      meta: [
        {
          title: 'The Blue Alliance - Brand',
        },
        {
          name: 'description',
          content:
            "Documentation of The Blue Alliance's logo and brand usage guidelines.",
        },
      ],
    };
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

const swatches = [
  {
    name: 'Primary',
    hex: '#3F51B5',
    rgb: '63 / 81 / 181',
    cmyk: '65 / 55 / 0 / 29',
    className: 'bg-brand text-white',
  },
  {
    name: 'Accent',
    hex: '#FFD600',
    rgb: '255 / 214 / 0',
    cmyk: '0 / 16 / 100 / 0',
    className: 'bg-brand-accent text-black',
  },
];

const logos = [
  { color: 'blue', backgroundClassName: 'bg-white' },
  { color: 'white', backgroundClassName: 'bg-brand' },
];

const logoFormats = ['svg', 'png', 'ai'];

const donts = [
  { image: 'rotate', text: 'rotate the logo.' },
  {
    image: 'stretch',
    text: 'change the logo’s proportion (e.g. skew, stretch or rotate).',
  },
  { image: 'change', text: 'change the elements.' },
  { image: 'colors', text: 're-color the colors.' },
  { image: 'shadow', text: 'add drop shadows or any other effects.' },
  { image: 'background', text: 'put on distracting backgrounds or colors.' },
];

function Brand(): React.JSX.Element {
  return (
    <div className="mx-auto max-w-4xl space-y-4 px-4">
      <section className="space-y-2">
        <h1 className="text-3xl font-medium">Brand Guidelines</h1>
        <p>
          Thanks for your interest our branding. We have a few guidelines for
          using our brand resources. Please take a moment to familiarize
          yourself with them.
        </p>
        <p>
          You can find downloadable assets in{' '}
          <a
            href="https://github.com/the-blue-alliance/the-blue-alliance-logo"
            target="_blank"
            rel="noopener noreferrer"
          >
            our GitHub
          </a>
          .
        </p>
      </section>

      <section className="space-y-2">
        <h2 className="text-2xl font-medium">Our Colors</h2>
        <p>Blue is our primary color. We use Yellow for accents.</p>
        <div className="flex max-w-xl">
          {swatches.map((swatch) => (
            <div
              key={swatch.name}
              className={`flex h-64 flex-1 flex-col items-center justify-center
              ${swatch.className}`}
            >
              <h3 className="text-lg font-medium">{swatch.name}</h3>
              <span>Hex: {swatch.hex}</span>
              <span>RGB: {swatch.rgb}</span>
              <span>CMYK: {swatch.cmyk}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-2xl font-medium">Our Logo</h2>
        <p>
          The logo can only appear in blue, white or black. You are free to use
          these logos when referring to or linking to The Blue Alliance. Please
          do not make derivatives of these logos or use them to brand unofficial
          The Blue Alliance products so we can maintain our visual identity.
        </p>
        <div className="flex flex-wrap gap-4">
          {logos.map((logo) => (
            <div
              key={logo.color}
              className="w-72 overflow-hidden rounded-md border border-border"
            >
              <div
                className={`flex h-44 items-center justify-center
                ${logo.backgroundClassName}`}
              >
                <img
                  width={180}
                  alt={`${logo.color} Lamp Logo`}
                  src={`/images/brand/logo-${logo.color}.svg`}
                />
              </div>
              <div
                className="flex divide-x divide-border border-t border-border"
              >
                {logoFormats.map((format) => (
                  <a
                    key={format}
                    className="flex-1 py-2 text-center font-bold uppercase
                      no-underline hover:bg-muted"
                    href={`/images/brand/logo-${logo.color}.${format}`}
                    aria-label={`Download ${logo.color} logo as ${format.toUpperCase()}`}
                    download
                  >
                    {format}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-medium">Please don’t do these things</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {donts.map((dont) => (
            <div key={dont.image}>
              <img
                className="mb-2 w-full"
                alt={`Example of what not to do: ${dont.text}`}
                src={`/images/brand/dont_${dont.image}.svg`}
              />
              <b>Don&apos;t</b> {dont.text}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
