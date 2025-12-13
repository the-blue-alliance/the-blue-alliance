import { Link, createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';

import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';

export const Route = createFileRoute('/apidocs')({
  component: ApiDocs,
  head: () => {
    return {
      meta: [
        {
          title: 'Developer APIs - The Blue Alliance',
        },
        {
          name: 'description',
          content:
            'An overview of the developer APIs offered by The Blue Alliance',
        },
      ],
    };
  },
});

function ApiDocs(): React.JSX.Element {
  const [inView, setInView] = useState(new Set<string>());

  const tocItems = [
    { slug: 'getting-started', label: 'Getting Started' },
    { slug: 'apiv3', label: 'Read API (v3)' },
    { slug: 'webhooks', label: 'Webhooks' },
    { slug: 'trusted', label: 'Write API' },
    { slug: 'guidelines', label: 'Developer Guidelines' },
  ];

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView} />
      <div className="basis-full py-8 md:basis-5/6">
        <div>
          <section>
            <h1 className="mb-2 text-3xl font-medium">
              The Blue Alliance Developer APIs
            </h1>
            <p>
              The Blue Alliance cares about making our data publicly accessible
              via our various APIs. We want to help inspire people to build
              their own projects and get started with data analysis and software
              development. This page explains the APIs we provide and how to get
              started using them.
            </p>
          </section>

          <section className="py-4">
            <h2 className="mb-2 text-2xl font-medium">Need Help?</h2>
            <p>
              Here are some areas where you can ask the TBA developer community
              for assistance if you run into trouble.
            </p>
            <ul className="mt-2 ml-8 list-disc">
              <li>
                <strong>Have questions?</strong> Reach out using resources on
                our <Link to="/contact">contact</Link> page.
              </li>
              <li>
                <strong>Found a bug or have a feature request?</strong> File an{' '}
                <a href="https://github.com/the-blue-alliance/the-blue-alliance/issues/new">
                  issue on GitHub.
                </a>
              </li>
              <li>
                <strong>Want to contribute?</strong>{' '}
                <a href="https://github.com/the-blue-alliance/the-blue-alliance">
                  Check out our code and send us a pull request!
                </a>
              </li>
            </ul>
          </section>

          <TableOfContentsSection
            id="getting-started"
            setInView={setInView}
            className="py-4"
          >
            <h2 className="mb-2 text-2xl font-medium">Getting Started</h2>
            <p>
              Before you get started using The Blue Alliance APIs, you need to
              be familiar with a few elements of web technology. The Blue
              Alliance APIs work by having your computer send a web request to
              our servers asking for some piece of data, and our servers send
              the data back to your computer. You can ask for information about
              teams or matches, or even send us information, like letting us
              know there&apos;s a robot photo we should add to our data set.
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
              machine-readable format for sending and receiving data. Most of
              the TBA APIs use JSON-formatted data, so you should find out how
              to parse JSON text in the language of your choice.
            </p>
            <p>
              Once you&apos;ve figured out how to make HTTPS requests, you will
              need to figure out how to manipulate request and response headers.
              These will be used to pass authentication keys to TBA and
              understand the cache life of returned data.
            </p>
          </TableOfContentsSection>

          <TableOfContentsSection
            id="apiv3"
            setInView={setInView}
            className="py-4"
          >
            <h2 className="mb-2 text-2xl font-medium">
              <Link to="/apidocs/v3">Read API (v3)</Link>
            </h2>
            <p>
              Most people want to pull event listings, team information, match
              results, or statistics from The Blue Alliance to use in their own
              application. The read API is the way to do this. This API exposes
              almost all of the data you see on TBA to your application in a
              machine-readable format called JSON.
            </p>
            <h3 className="mt-4 mb-2 text-xl">API Endpoint</h3>
            <p>
              All requests should be made to the base URL:{' '}
              <code>https://www.thebluealliance.com/api/v3</code>.
            </p>
            <h3 className="mt-4 mb-2 text-xl">Authentication</h3>
            <h4 className="text-l mb-2">
              <code>X-TBA-Auth-Key</code> Header
            </h4>
            <p>
              Generate an access token on your{' '}
              <Link to="/account">Account Dashboard</Link> in the Read API Keys
              section. This key needs to be passed along with each request you
              make in the header (or URL parameter) <code>X-TBA-Auth-Key</code>.
            </p>
            <p>
              If you are logged in to your TBA account, you can access the API
              without a key by simply navigating to an API URL in your web
              browser.
            </p>
            <h3 className="mt-4 mb-2 text-xl">Caching</h3>
            <h4 className="text-l mb-2">
              <code>ETag</code> and <code>If-None-Match</code> Headers
            </h4>
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
            <h4 className="text-l mt-4 mb-2">
              <code>Cache-Control</code> Header
            </h4>
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
            <h3 className="mt-4 mb-2 text-xl">Client Libraries</h3>
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
          </TableOfContentsSection>

          <TableOfContentsSection
            id="webhooks"
            setInView={setInView}
            className="py-4"
          >
            <h2 className="mb-2 text-2xl font-medium">
              <a href="/apidocs/webhooks">Webhooks</a>
            </h2>
            <p>
              The TBA API also includes support for{' '}
              <a href="https://en.wikipedia.org/wiki/Webhook">webhooks</a>, or
              HTTP callbacks. When an item of interest changes, TBA can send a
              HTTP request to your server, allowing your application to react
              instantly to the change. This can save both your client and our
              server time and processing power, as it can reduce the need to
              poll the API. See{' '}
              <a href="/apidocs/webhooks">our webhook documentation page</a> for
              more information.
            </p>
          </TableOfContentsSection>

          <TableOfContentsSection
            id="trusted"
            setInView={setInView}
            className="py-4"
          >
            <h2 className="mb-2 text-2xl font-medium">
              <a href="/apidocs/trusted/v1">Write API (v1)</a>
            </h2>
            <p>
              The Blue Alliance provides a Write API, called the Trusted API,
              which allows users to import data to The Blue Alliance for
              archival. For example, many offseason events use the Trusted API
              to provide real-time match results to their audience. To get
              started, you need to{' '}
              <a href="/request/apiwrite">request access tokens</a> for your
              desired event. These need to be used when constructing each
              request.
            </p>
            <p>
              To see the complete specification of the trusted API, refer to the{' '}
              <a href="/apidocs/trusted/v1">full documentation</a>.
            </p>
          </TableOfContentsSection>

          <TableOfContentsSection
            id="guidelines"
            setInView={setInView}
            className="py-4"
          >
            <h2 className="mb-2 text-2xl font-medium">
              TBA Developer Guidelines
            </h2>
            <p>
              We&apos;re excited to see you building things on top of The Blue
              Alliance&apos;s APIs! We love seeing the creativity and utility in
              these projects. We have a few developer guidelines to help guide
              your work.
            </p>
            <ol className="mt-4 ml-8 list-decimal space-y-4">
              <li>
                <strong>Branding</strong>
                <ul className="ml-6 list-disc">
                  <li>
                    We want people to know which apps are official The Blue
                    Alliance apps, and which apps are powered by our API, but
                    not supported by us.
                  </li>
                  <li>
                    Please do not use &quot;The Blue Alliance&quot;,
                    &quot;TBA&quot;, or The Blue Alliance lamp logo in the name
                    or brand identity of your app.
                  </li>
                  <li>
                    If you&apos;d like your project to become an official part
                    of The Blue Alliance, please{' '}
                    <Link to="/contact">reach out to us</Link>. We&apos;d love
                    to talk more!
                  </li>
                </ul>
              </li>
              <li>
                <strong>Attribution</strong>
                <ul className="ml-6 list-disc">
                  <li>
                    Please note that your project is &quot;Powered by The Blue
                    Alliance&quot; with a link back to{' '}
                    <Link to="/">thebluealliance.com</Link>. This helps people
                    discover our site, lets your users know where to report data
                    issues, and helps more people get inspired to build on top
                    of our APIs.
                  </li>
                  <li>
                    If you offer links out of your app for more details about
                    teams, events, or other data, we ask that you consider
                    linking back to corresponding pages on The Blue Alliance.
                  </li>
                </ul>
              </li>
            </ol>
          </TableOfContentsSection>
        </div>
      </div>
    </div>
  );
}
