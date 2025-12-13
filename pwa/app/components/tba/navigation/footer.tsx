import { Link } from '@tanstack/react-router';
import { Fragment } from 'react/jsx-runtime';

const links = [
  {
    label: 'GitHub',
    href: 'https://github.com/the-blue-alliance/the-blue-alliance',
  },
  { label: 'About us', href: '/about' },
  { label: 'Donate', href: '/donate' },
  { label: 'Contact', href: '/contact' },
  { label: 'Thanks', href: '/thanks' },
  { label: 'Add Data', href: '/add-data' },
  { label: 'API Documentation', href: '/apidocs' },
  {
    label: 'Blog',
    href: 'https://blog.thebluealliance.com',
  },
  { label: 'Privacy Policy', href: '/legal/privacy' },
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
          {links.map(({ label, href }, index) => (
            <Fragment key={label}>
              {href.startsWith('http') ? (
                <a
                  key={label}
                  className="text-gray-800"
                  href={href}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {label}
                </a>
              ) : (
                <Link key={label} className="text-gray-800" to={href}>
                  {label}
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
          <p>© {new Date().getFullYear()} The Blue Alliance</p>

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
