import { Link, createFileRoute } from '@tanstack/react-router';

import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/thanks')({
  headers: publicCacheControlHeaders(),
  component: Thanks,
});

function Thanks(): React.JSX.Element {
  return (
    <div className="container max-w-4xl py-8">
      <div className="typeset">
        <h1>Thanks</h1>
        <p>
          The Blue Alliance is a non-profit organization that relies on
          open-source contributions, volunteers, and our sponsors to keep the
          site running.
        </p>
        <p>
          If you would like to support the site, please consider{' '}
          <Link to="/donate">making a donation.</Link>
        </p>

        <h2>Contributors</h2>
        <p>
          Thanks to our code contributors for our{' '}
          <a href="https://github.com/the-blue-alliance/the-blue-alliance/graphs/contributors">
            web app,
          </a>{' '}
          <a href="https://github.com/the-blue-alliance/the-blue-alliance-android/graphs/contributors">
            Android app,
          </a>{' '}
          and{' '}
          <a href="https://github.com/the-blue-alliance/the-blue-alliance-ios/graphs/contributors">
            iOS app
          </a>
          ; and to our data submitters and data moderators.
        </p>

        <h2>Sponsors</h2>
        <p>Thank you to our generous sponsors for allowing our app to run.</p>
        <h3>Platinum</h3>
        <ul>
          <li>
            <a href="https://www.andymark.com/" title="AndyMark">
              AndyMark
            </a>
          </li>
        </ul>
        <h3>Gold</h3>
        <ul>
          <li>
            <a href="https://www.thethriftybot.com/" title="The Thrifty Bot">
              The Thrifty Bot
            </a>
          </li>
        </ul>

        <h2>Built With</h2>
        <ul>
          <li>
            <a href="https://tanstack.com/start" title="TanStack Start">
              TanStack Start
            </a>
            , a full-stack web framework
          </li>
          <li>
            <a href="https://tailwindcss.com/" title="Tailwind CSS">
              Tailwind CSS
            </a>
            , a utility-first CSS framework
          </li>
        </ul>
      </div>
    </div>
  );
}
