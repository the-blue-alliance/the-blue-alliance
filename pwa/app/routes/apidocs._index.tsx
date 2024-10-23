import { Link } from '@remix-run/react';

export default function ApiDocs(): React.JSX.Element {
  return (
    <>
      <div className="flex flex-col divide-y [&_*]:mt-4">
        <div>
          <h1 className="text-3xl font-medium">
            The Blue Alliance Developer APIs
          </h1>
          <p>
            The Blue Alliance cares about making our data publicly accessible
            via our various APIs. We want to help inspire people to build their
            own projects and get started with data analysis and software
            development. This page explains the APIs we provide and how to get
            started using them.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Need Help?</h3>
          <p>
            Here are some areas where you can ask the TBA developer community
            for assistance if you run into trouble. for guidance.
          </p>
          <ul>
            <li className="list-disc">
              <p>
                Have questions? Reach out using resources on our{' '}
                <Link to="/contact">contact</Link> page.
              </p>
            </li>
            <li className="list-disc">
              <p>
                Found a bug or have a feature request? File an{' '}
                <a href="https://github.com/the-blue-alliance/the-blue-alliance/issues/new">
                  issue on GitHub.
                </a>{' '}
              </p>
            </li>
            <li className="list-disc">
              <p>
                Want to contribute?{' '}
                <a href="https://github.com/the-blue-alliance/the-blue-alliance">
                  Check out our code and send us a pull request!
                </a>{' '}
              </p>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-2xl">Getting Started</h3>
          <p>
            Before you get started using The Blue Alliance APIs, you need to be
            familiar with a few elements of web technology. The Blue Alliance
            APIs work by having your computer send a web request to our servers
            asking for some piece of data, and our servers send the data back to
            your computer. You can ask for information about teams or matches,
            or even send us information, like letting us know there&apos;s a
            robot photo we should add to our data set.
          </p>
          <p>
            First, you need some way of sending HTTPS Requests to The Blue
            Alliance&apos;s servers. This will be your primary means of
            communication with TBA. For testing purposes, your web browser may
            suffice. For more advanced applications, you may want to use an
            external library, such as{' '}
            <a href="https://www.w3schools.com/jquery/jquery_ajax_intro.asp">
              jQuery
            </a>{' '}
            (Javascript),{' '}
            <a href="http://docs.python-requests.org/en/master/">Requests</a>{' '}
            (Python), or <a href="https://square.github.io/okhttp/">OkHttp</a>{' '}
            (Java), or others.
          </p>
          <p>
            You will also need to be familiar with{' '}
            <a href="https://en.wikipedia.org/wiki/Json">JSON</a>, a
            machine-readable format for sending and receiving data. Most of the
            TBA APIs use JSON-formatted data, so you should find out how to
            parse JSON text in the language of your choice.
          </p>
          <p>
            Once you&apos;ve figured out how to make HTTPS requests, you will
            need to figure out how to manipulate request and response headers.
            These will be used to pass authentication keys to TBA and understand
            the cache life of returned data.
          </p>
        </div>

        <div>
          <div>
            <h3 className="text-2xl">
              <Link to="/apidocs/v3">Read API (v3)</Link>
            </h3>
            <p>
              Most people want to pull event listings, team information, match
              results, or statistics from The Blue Alliance to use in their own
              application. The read API is the way to do this. This API exposes
              almost all of the data you see on TBA to your application in a
              machine-readable format called JSON.
            </p>
          </div>

          <div>
            <h4 className="text-xl">API Endpoint</h4>
            <p>
              All requests should be made to the base URL:{' '}
              <code>https://www.thebluealliance.com/api/v3</code>.
            </p>
          </div>

          <div>
            <h4 className="text-xl">Authentication</h4>
            <h5 className="text-l">
              <code>X-TBA-Auth-Key</code> Header
            </h5>
            <p>
              Generate an access token on your{' '}
              <Link to="/account">Account Dashboard</Link> in the Read API Keys
              section. This key needs to be passed along with each request you
              make in the header (or URL parameter) <code>X-TBA-Auth-Key</code>.
            </p>
            <p>
              If you are logged in to your TBA account, you can access the API
              without a key by simply navigating to an API URL in your web
              browser
            </p>
          </div>

          <div>
            <h4 className="text-xl">Caching</h4>
            <h5 className="text-l">
              <code>ETag</code> and <code>If-None-Match</code> Headers
            </h5>
            <p>
              All API responses have an <code>Etag</code> header which specifies
              the version of the most recent response. When making repeated
              calls to a particular endpoint, you should set the{' '}
              <code>If-None-Match</code> header in your request to the{' '}
              <code>Etag</code> value from the previous call to that endpoint.
              On the first call, <code>If-None-Match</code> does not need to be
              set.
            </p>
            <p>
              Consumers of the TBA API are highly encouraged to make use of
              these headers. If the server determines that no data has been
              updated, it returns a <code>304 Not Modified</code> response with
              an empty body, saving both the server and the consumer time and
              bandwidth.
            </p>
            <p>
              For more details, see{' '}
              <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/ETag">
                Mozilla&apos;s ETag reference
              </a>
              .
            </p>
            <h5 className="text-l">
              <code>Cache-Control</code> Header
            </h5>
            <p>
              If your application makes many queries to the TBA API and you are
              capable of caching the results locally, the{' '}
              <code>Cache-Control</code> header will provide guidance on how
              long the API response can remain valid in a local cache. In
              particular, the <code>max-age</code> value in the{' '}
              <code>Cache-Control</code> header contains the number of seconds
              the API result should be considered valid for. See also{' '}
              <a href="https://developers.google.com/web/fundamentals/performance/optimizing-content-efficiency/http-caching?hl=en#cache-control">
                Google&apos;s Cache-Control reference
              </a>
              .
            </p>
          </div>

          <div>
            <h4 className="text-xl">Client Libraries</h4>
            <p>
              The Blue Alliance automatically builds and publishes client
              libraries to make it easier for you to get started using APIv3.
              The libraries are automatically generated by{' '}
              <a href="https://swagger.io/swagger-codegen/">Swagger Codegen</a>{' '}
              and are not provided with any guarantee of support from The Blue
              Alliance and are not guaranteed to be complete implementations of
              the API. They are merely provided as a convenience to developers
              looking to get started and can be found{' '}
              <a href="https://github.com/TBA-API">on the TBA-API GitHub</a>.
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-2xl">
            <Link to="/apidocs/webhooks">Webhooks</Link>
          </h3>
          <p>
            The TBA API also includes support for{' '}
            <a href="https://en.wikipedia.org/wiki/Webhook">webhooks</a>, or
            HTTP callbacks. When an item of interest changes, TBA can send a
            HTTP request to your server, allowing your application to react
            instantly to the change. This can save both your client and our
            server time and processing power, as it can reduce the need to poll
            the API. See{' '}
            <Link to="/apidocs/webhooks">our webhook documentation page</Link>{' '}
            for more information.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">
            <Link to="/apidocs/trusted/v1">Write API (v1)</Link>
          </h3>
          <p>
            The Blue Alliance provides a Write API, called the Trusted API,
            which allows users to import data to The Blue Alliance for archival.
            For example, many offseason events use the Trusted API to provide
            real-time match results to their audience. To get started, you need
            to <Link to="/request/apiwrite">request access tokens</Link> for
            your desired event. These need to be used when constructing each
            request.
          </p>
          <p>
            To see the complete specification of the trusted API, refer to the{' '}
            <Link to="/apidocs/trusted/v1">full documentation</Link>.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">
            <a href="https://github.com/the-blue-alliance/the-blue-alliance-data">
              Data Archives
            </a>
          </h3>
          <p>
            If you&apos;re looking to run SQL queries over the TBA database, you
            can use this{' '}
            <a href="https://www.thebluealliance.com/bigquery">BigQuery</a>{' '}
            dataset. This contains a full replica of the TBA database, so the
            possibilities are endless!
          </p>
          <p>
            If these APIs are too complex for your application, The Blue
            Alliance also provides periodic data archives in comma separated
            value (CSV) format. The data provided here is less detailed, but is
            simpler to use in someething like a spreadsheet.
          </p>
          <p>
            You can find these data archives on
            <a href="https://github.com/the-blue-alliance/the-blue-alliance-data">
              {' '}
              The Blue Alliance&apos;s TBA Data Repository
            </a>
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Developer Guidlines</h3>
          <p>
            We&apos;re excited to see you building things on top of The Blue
            Alliance&apos;s APIs! We love seeing the creativity and utility in
            these projects. We have a few developer guidelines to help guide
            your work.
          </p>

          <div>
            <h4 className="text-xl">1. Branding</h4>
            <ul>
              <li className="list-disc">
                <p>
                  We want people to know which apps are official The Blue
                  Alliance apps, and which apps are powered by our API, but not
                  supported by us.
                </p>
              </li>
              <li className="list-disc">
                <p>
                  Please do not use “The Blue Alliance”, “TBA”, or The Blue
                  Alliance lamp logo in the name or brand identity of your app.
                </p>
              </li>
              <li className="list-disc">
                <p>
                  If you&apos;d like your project to become an official part of
                  The Blue Alliance, please{' '}
                  <Link to="/contact">reach out to us</Link>. We&apos;d love to
                  talk more!
                </p>
              </li>
            </ul>
            <h4 className="text-xl">2. Attribution</h4>
            <ul>
              <li className="list-disc">
                <p>
                  Please note that your project is “Powered by The Blue
                  Alliance” with a link back to{' '}
                  <Link to="/">thebluealliance.com</Link>. This helps people
                  discover our site, lets your users know where to report data
                  issues, and helps more people get inspired to build on top of
                  our APIs.
                </p>
              </li>
              <li className="list-disc">
                <p>
                  If you offer links out of your app for more details about
                  teams, events, or other data, we ask that you consider linking
                  back to corresponding pages on The Blue Alliance.
                </p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}
