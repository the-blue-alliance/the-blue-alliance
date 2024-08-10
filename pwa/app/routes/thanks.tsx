export default function Thanks(): JSX.Element {
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
            <a href="/donate">making a donation.</a>
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Contributors</h3>
          <p>
            Thanks to our code contributors for our{' '}
            <a href="/https://github.com/the-blue-alliance/the-blue-alliance/graphs/contributors">
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
            <li>
              <p className="pl-1">
                <a href="https://www.andymark.com/" title="AndyMark">
                  AndyMark
                </a>
              </p>
            </li>
          </ul>
          <h4 className="text-xl">Gold</h4>
          <ul>
            <li className="pl-1">
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
            <li className="pl-1">
              <p>
                <a
                  href="http://www.komodomedia.com/download/#social-network-icon-pack"
                  title="Komodo Media"
                >
                  Komodo Media
                </a>
                &apos;s social media icons
              </p>
            </li>
            <li className="pl-1">
              <p>
                <a href="https://github.com/twbs/bootstrap" title="Bootstrap">
                  Bootstrap
                </a>
                &apos;s HTML CSS JS framework
              </p>
            </li>
            <li className="pl-1">
              <p>
                <a href="https://react.dev/" title="React">
                  React
                </a>
                &apos;s web development framework
              </p>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}
