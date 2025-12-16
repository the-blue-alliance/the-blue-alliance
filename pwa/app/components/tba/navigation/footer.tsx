import { Link } from '@tanstack/react-router';
import { Monitor, Moon, Sun } from 'lucide-react';
import { Fragment } from 'react/jsx-runtime';

import GithubIcon from '~icons/logos/github-icon';

import { Button } from '~/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import andymarkLogo from '~/images/images/andymark-logo.png';
import { useTheme } from '~/lib/theme';
import { FileRouteTypes } from '~/routeTree.gen';

interface InternalLink {
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  label: string;
  to: FileRouteTypes['to'];
}

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

function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          aria-label="Toggle theme"
        >
          {resolvedTheme === 'dark' ? (
            <Moon className="size-4" />
          ) : (
            <Sun className="size-4" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => setTheme('light')}
          className={theme === 'light' ? 'bg-accent' : ''}
        >
          <Sun className="mr-2 size-4" />
          Light
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('dark')}
          className={theme === 'dark' ? 'bg-accent' : ''}
        >
          <Moon className="mr-2 size-4" />
          Dark
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('system')}
          className={theme === 'system' ? 'bg-accent' : ''}
        >
          <Monitor className="mr-2 size-4" />
          System
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
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
        bg-gray-50 dark:bg-gray-900"
    >
      <div
        className="mx-auto w-full px-4 sm:max-w-160 md:max-w-3xl md:px-8
          lg:max-w-5xl"
      >
        <div className="flex flex-wrap gap-2 py-6 text-center text-sm">
          {links.map((link, index) => (
            <Fragment key={link.label}>
              {'href' in link ? (
                <a
                  key={link.label}
                  className="flex items-center gap-1 text-gray-800
                    hover:underline dark:text-gray-200"
                  href={link.href}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {link.icon && <link.icon className="size-3" />}
                  {link.label}
                </a>
              ) : (
                <Link
                  key={link.label}
                  className="flex items-center gap-1 text-gray-800
                    hover:underline dark:text-gray-200"
                  to={link.to}
                >
                  {link.icon && <link.icon className="size-3" />}
                  {link.label}
                </Link>
              )}
              {index < links.length - 1 && (
                <span className="text-gray-300 dark:text-gray-600">/</span>
              )}
            </Fragment>
          ))}
        </div>

        <div
          className="relative isolate flex justify-between gap-0.5 border-t
            border-gray-600/10 py-4 text-sm max-md:flex-col md:items-center"
        >
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <span className="text-gray-600 dark:text-gray-400">|</span>
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
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400">
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
