import { Link } from '@remix-run/react';

export default function Thanks(): React.JSX.Element {
  return (
    <>
      <div className="flex flex-col divide-y [&_*]:mt-4">
        <div>
          <h1 className="text-3xl font-medium">Thanks</h1>
          <p>
            The Blue Alliance is a non-profit organization that relies on
            open-source contributions, volunteers, and our sponsors to keep the
            site running.
          </p>
          <p>
            If you would like to support the site, please consider{' '}
            <Link to="/donate">making a donation.</Link>
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Contributors</h3>
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
        </div>

        <div>
          <h3 className="text-2xl">Sponsors</h3>
          <p>Thank you to our generous sponsors for allowing our app to run.</p>
          <h4 className="text-xl">Platinum</h4>
          <ul>
            <li className="list-disc">
              <p>
                <a href="https://www.andymark.com/" title="AndyMark">
                  AndyMark
                </a>
              </p>
            </li>
          </ul>
          <h4 className="text-xl">Gold</h4>
          <ul>
            <li className="list-disc">
              <p>
                <a
                  href="https://www.thethriftybot.com/"
                  title="The Thrifty Bot"
                >
                  The Thrifty Bot
                </a>
              </p>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-2xl">Built With</h3>
          <ul>
            <li className="list-disc">
              <p>
                <a href="https://remix.run/" title="Remix">
                  Remix
                </a>
                &apos;s full stack web development framework
              </p>
            </li>
            <li className="list-disc">
              <p>
                <a href="https://tailwindcss.com/" title="Tailwind">
                  Tailwind
                </a>
                &apos;s CSS framework
              </p>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}
