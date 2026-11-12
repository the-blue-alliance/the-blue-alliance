import { Link, createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';

import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/faq')({
  headers: publicCacheControlHeaders(),
  component: Faq,
  head: () => {
    return {
      meta: [
        {
          title: 'Frequently Asked Questions - The Blue Alliance',
        },
        {
          name: 'description',
          content: 'The Blue Alliance Frequently Asked Questions',
        },
      ],
    };
  },
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

const tocItems = [
  { slug: 'data-sources', label: 'Data Sources' },
  { slug: 'data-freshness', label: 'Data Freshness' },
  { slug: 'data-accuracy', label: 'Data Accuracy' },
  { slug: 'team-data', label: 'Team Data' },
  { slug: 'event-data', label: 'Event Data' },
  { slug: 'feature-requests', label: 'Feature Requests' },
];

function Faq(): React.JSX.Element {
  const [inView, setInView] = useState(new Set<string>());

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView} />
      <div className="basis-full space-y-4 md:basis-5/6">
        <section>
          <h1 className="mb-2 text-3xl font-medium">
            Frequently Asked Questions
          </h1>
          <p>
            This page provides answers to some of the most Frequently Asked
            Questions about TBA.
          </p>
        </section>

        <TableOfContentsSection
          id="data-sources"
          setInView={setInView}
          className="space-y-2"
        >
          <h2 className="text-2xl font-medium">Data Sources</h2>
          <p>
            TBA sources its data from a number of sources depending on many
            factors.
          </p>
          <div className="grid gap-x-8 gap-y-4 md:grid-cols-2">
            <div className="space-y-2">
              <h3 className="text-xl font-medium">
                Data from Official Sources
              </h3>
              <p>
                TBA gathers a great deal of information from official sources
                published by <em>FIRST</em>. This includes information about
                teams, events, match results, awards, as well as many match
                videos. Generally, official sources are available and used for
                more recent seasons.
              </p>
              <p>
                Teams themselves can access and update some team-related data on
                TBA by using the <a href="/mod">Team Admin Dashboard</a>.
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="text-xl font-medium">Crowdsourced Data</h3>
              <p>
                TBA also gathers a great deal of information from crowdsourced
                sources. This includes information such as robot pictures,
                reveal videos, robot CAD files, and social media links.
                Additionally, some match videos recorded by partners or teams
                themselves are included.
              </p>
              <p>
                Users will see links on various pages throughout TBA to suggest
                additional information, videos, or images.
              </p>
              <p>
                Finally, a great deal of historical information available on TBA
                is not available from official sources and is instead
                crowdsourced from the community.
              </p>
            </div>
          </div>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="data-freshness"
          setInView={setInView}
          className="space-y-2"
        >
          <h2 className="text-2xl font-medium">Data Freshness</h2>
          <p>
            TBA strives to have the most up-to-date data available. For data
            provided by <em>FIRST</em>, TBA will make every effort to ensure
            that data is accurate and up to date, while maintaining an
            economically viable service to the community. Two key parts of that
            process are the refresh-rate and caching of data.
          </p>
          <p>
            TBA regularly updates current-season data, while providing frequent
            updates to events-in-progress and less frequent updates to other
            events. Events in progress will often update within minutes, if not
            faster, while events that have concluded or not begun may take 24
            hours, or longer, to update.
          </p>
          <p>
            Please note that offseason or unofficial events may require manual
            updates from the event organizer.
          </p>
          <p>
            Aside from the data refresh rate, TBA uses an aggressive caching
            system to provide our service at scale. As a result, data may be
            provided from one of our caches and appear stale temporarily. This
            is normal and expected behavior. You can check this by looking at
            the bottom of the page for the date and time each page was
            generated. Also refer to our{' '}
            <Link to="/apidocs">API reference</Link> for more information on API
            response caching.
          </p>
          <p>
            If you notice out of date data, please{' '}
            <Link to="/contact">contact us</Link> to help us keep TBA up to
            date.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="data-accuracy"
          setInView={setInView}
          className="space-y-2"
        >
          <h2 className="text-2xl font-medium">Data Accuracy</h2>
          <p>
            TBA strives to have the most up-to-date and accurate data available.
            For data provided by <em>FIRST</em>, TBA will make every effort to
            ensure that data is accurate and up to date. If <em>FIRST</em>
            -provided data is incorrect, we encourage the affected team to
            contact <em>FIRST</em> directly to correct the information.
          </p>
          <p>
            For crowdsourced data, please <Link to="/contact">Contact Us</Link>{' '}
            with any data issues.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="team-data"
          setInView={setInView}
          className="space-y-2"
        >
          <h2 className="text-2xl font-medium">Updating Team Data</h2>
          <p>
            Teams seeking to update their team data shown on TBA must contact{' '}
            <em>FIRST</em> to update any of the following: Team name, location
            (city, state, country), sponsor information, or avatar. Images, team
            videos, and social media links can be updated or removed using the{' '}
            <a href="/mod">Team Admin Dashboard</a> and any user can suggest new
            videos or links from the team page, subject to moderation.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="event-data"
          setInView={setInView}
          className="space-y-2"
        >
          <h2 className="text-2xl font-medium">Updating Event Data</h2>
          <p>
            If you wish to add to, or correct, historical event information not
            currently provided by <em>FIRST</em>, you can{' '}
            <Link to="/contact">contact us</Link> providing a description of the
            change you wish made and any supporting documentation. For offseason
            or unofficial events that are not using FMS Sync, please contact the
            event organizer and ask them to reach out to us. For events with
            data provided by <em>FIRST</em>, please contact <em>FIRST</em>{' '}
            directly to correct the information.
          </p>
          <p>
            In the rare case where event information has been changed after the
            conclusion of the event, TBA may retain older or incorrect
            information for some time. If several days have passed, please{' '}
            <Link to="/contact">contact us</Link> to request that the
            information be updated.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="feature-requests"
          setInView={setInView}
          className="space-y-2"
        >
          <h2 className="text-2xl font-medium">Feature Requests</h2>
          <p>
            The Blue Alliance welcomes feature requests from the community. If
            you have an idea for a new feature or improvement, please open an
            issue on our{' '}
            <a href="https://github.com/the-blue-alliance">GitHub page</a> with
            your suggestion. We value your input and will consider all valid
            feature requests for future development.
          </p>
          <p>
            The Blue Alliance is a community-driven Open Source Project. We
            welcome contributions from the community to help improve the
            platform and make it more useful for everyone.
          </p>
        </TableOfContentsSection>
      </div>
    </div>
  );
}
