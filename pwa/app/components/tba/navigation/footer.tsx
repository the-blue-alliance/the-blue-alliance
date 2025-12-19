import { Link, LinkOptions } from '@tanstack/react-router';
import { MoonIcon, SunIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Fragment } from 'react/jsx-runtime';

import GithubIcon from '~icons/logos/github-icon';

import andymarkLogo from '~/images/images/andymark-logo.png';
import { useTheme } from '~/lib/theme';

type InternalLink = {
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
} & Pick<LinkOptions, 'to' | 'params'>;

interface ExternalLink {
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
  href: string;
}

type NavigationLink = InternalLink | ExternalLink;

const links: NavigationLink[] = [
  {
    icon: GithubIcon,
    label: 'GitHub',
    href: 'https://github.com/the-blue-alliance/the-blue-alliance',
  },
  { label: 'About us', to: '/about' },
  { label: 'Donate', to: '/donate' },
  { label: 'Contact', to: '/contact' },
  { label: 'Thanks', to: '/thanks' },
  { label: 'Add Data', to: '/add-data' },
  { label: 'API Documentation', to: '/apidocs' },
  {
    label: 'Blog',
    href: 'https://blog.thebluealliance.com',
  },
  { label: 'Privacy Policy', to: '/privacy' },
];

// Commit hash is string-replaced, so we need to ignore eslint and typescript errors.
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error
const commitHash = __COMMIT_HASH__ as string;

const themes = [['light', SunIcon] as const, ['dark', MoonIcon] as const];

function ThemeToggle() {
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState<boolean>(false);
  const value = mounted ? resolvedTheme : null;

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <button
      className="group inline-flex cursor-pointer items-center rounded-full
        border p-1"
      aria-label="Toggle Theme"
      onClick={() => setTheme(value === 'light' ? 'dark' : 'light')}
    >
      {themes.map(([key, Icon]) => {
        return (
          <Icon
            key={key}
            fill="currentColor"
            data-active={value === key}
            className={`size-6.5 rounded-full p-1.5 text-muted-foreground
            transition-colors group-hover:text-accent-foreground
            data-[active=true]:bg-black/5
            data-[active=true]:text-accent-foreground
            dark:data-[active=true]:bg-accent`}
          />
        );
      })}
    </button>
  );
}

export const Footer = () => {
  const renderTime = new Date().toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
  });

  return (
    <footer
      className="mt-(--footer-inset-top) flex flex-col space-y-3 border-t
        bg-neutral-50 dark:bg-neutral-900"
    >
      <div
        className="mx-auto w-full px-4 sm:max-w-160 md:max-w-3xl md:px-8
          lg:max-w-5xl"
      >
        <div className="flex items-center gap-8">
          <div className="flex flex-1 flex-wrap gap-2 py-6 text-center text-sm">
            {links.map((link, index) => (
              <Fragment key={link.label}>
                {'href' in link ? (
                  <a
                    key={link.label}
                    className="flex items-center gap-1 text-neutral-800
                      hover:underline dark:text-neutral-200"
                    href={link.href}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    {link.icon && (
                      <link.icon className="size-3 *:fill-current" />
                    )}
                    {link.label}
                  </a>
                ) : (
                  <Link
                    key={link.label}
                    className="flex items-center gap-1 text-neutral-800
                      hover:underline dark:text-neutral-200"
                    to={link.to}
                  >
                    {link.icon && <link.icon className="size-3" />}
                    {link.label}
                  </Link>
                )}
                {index < links.length - 1 && (
                  <span className="text-neutral-300 dark:text-neutral-600">
                    /
                  </span>
                )}
              </Fragment>
            ))}
          </div>
          <ThemeToggle />
        </div>
        <div
          className="relative isolate flex justify-between gap-0.5 border-t
            border-neutral-600/10 py-5 text-sm max-md:flex-col md:items-center"
        >
          <span>
            Thanks to our platinum sponsor
            <a
              href="https://www.andymark.com/"
              target="_blank"
              rel="noreferrer noopener"
            >
              <img
                src={andymarkLogo}
                alt="AndyMark"
                className="ml-2 inline h-4"
              />
            </a>
          </span>

          <p className="text-xs text-neutral-600 dark:text-neutral-400">
            Generated on {renderTime}. Commit:{' '}
            <a
              href={`https://github.com/the-blue-alliance/the-blue-alliance/commit/${commitHash}`}
              target="_blank"
              rel="noreferrer"
            >
              {commitHash}
            </a>
            .
          </p>
        </div>
      </div>
    </footer>
  );
};
