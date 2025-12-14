import { Link } from '@tanstack/react-router';
import { Fragment } from 'react/jsx-runtime';

import GithubIcon from '~icons/logos/github-icon';

import andymarkLogo from '~/images/images/andymark-logo.png';
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
  { label: 'Privacy Policy', to: '/legal/privacy' },
];

// Commit hash is string-replaced, so we need to ignore eslint and typescript errors.
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-expect-error
const commitHash = __COMMIT_HASH__ as string;

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
    <footer className="mt-16 flex flex-col space-y-3 border-t bg-gray-50">
      <div
        className="mx-auto w-full px-6 sm:max-w-160 md:max-w-3xl md:px-8
          lg:max-w-5xl"
      >
        <div className="flex flex-wrap gap-2 py-6 text-center text-sm">
          {links.map((link, index) => (
            <Fragment key={link.label}>
              {'href' in link ? (
                <a
                  key={link.label}
                  className="flex items-center gap-1 text-gray-800
                    hover:underline"
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
                    hover:underline"
                  to={link.to}
                >
                  {link.icon && <link.icon className="size-3" />}
                  {link.label}
                </Link>
              )}
              {index < links.length - 1 && (
                <span className="text-gray-300">/</span>
              )}
            </Fragment>
          ))}
        </div>

        <div
          className="relative isolate flex justify-between border-t
            border-gray-600/10 py-6 text-sm max-md:flex-col md:items-center"
        >
          <div>
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
          </div>
          <p className="text-xs text-gray-600">
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
