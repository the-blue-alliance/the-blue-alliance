import { Link, createFileRoute } from '@tanstack/react-router';

import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/add-data')({
  headers: publicCacheControlHeaders(),
  component: AddData,
});

function AddData(): React.JSX.Element {
  return (
    <div className="container max-w-4xl py-8">
      <div className="typeset">
        <h1>Add Data to TBA!</h1>
        <p>
          Do you have some data you&apos;d like to add to The Blue Alliance?
          This page will provide you with the resources you need to help
          contribute to TBA.
        </p>

        <h2>Adding Match Videos</h2>
        <p>
          If you have links to YouTube recordings of match video, you can link
          them on TBA. You can suggest videos individually from the detail page
          for a given match, and if you have a YouTube playlist for an event,
          click the &quot;Add Match Videos!&quot; button on the
          &quot;Event&quot; page and input the playlist link. If you&apos;re
          webcasting and archiving an event and want to directly add videos as
          they get uploaded, you can{' '}
          <a href="/request/apiwrite">request write keys.</a>
        </p>

        <h2>Event Webcasts</h2>
        <p>
          If you have the link to the webcast for an event, you can suggest it
          from the event&apos;s detail page, or from The Blue Alliance homepage
          if the event is currently active. We make an effort to support many
          stream types, but Twitch.tv, Livestream, and YouTube are most common.
        </p>

        <h2>Team Media</h2>
        <p>
          You can suggest various types of team media to TBA from a team&apos;s
          detail page in a specific year. You can suggest robot pictures, reveal
          videos, and robot CAD. Team social media accounts, like Twitter,
          Facebook, Instagram, GitHub, and GitLab are not year-specific, and
          persist from year to year.
        </p>

        <h2>Adding a New Offseason Event</h2>
        <p>
          Do you know of an offseason event missing from TBA? You can suggest an
          event to be added <a href="/suggest/offseason">here</a>. The request
          will be reviewed and added shortly.
        </p>

        <h2>Adding Offseason Event Results</h2>
        <h3>FMS Sync</h3>
        <p>
          Offseason events have the ability to have their match results, team
          list, and other data synchronized to <em>FIRST</em> Headquarters
          infrastructure using the same mechanisms that are used in-season. If
          your offseason-event is using FMS Sync, it is <em>automatically</em>{' '}
          added to TBA.
        </p>
        <p>
          Match videos, livestreams, and awards would still need to be added
          using the mechanisms listed above though.
        </p>
        <h3>Offline FMS</h3>
        <p>
          If your offseason event does <em>not</em> have FMS Sync back to
          Headquarters, that&apos;s not an issue either. You can{' '}
          <a href="/request/apiwrite">request write keys</a> and post individual
          data points during an event using the{' '}
          <a href="/eventwizard2">Event Wizard</a> to get results in a timely
          manner.
        </p>
        <p>
          Alternately, get the FMS Reports exported before you tear down your
          field. TBA can take the Excel files and import them to get match data
          after the fact, to get as much historical data as possible.
        </p>

        <h2>FMS Reports</h2>
        <p>
          We can also import FMS Report exports into The Blue Alliance. You can
          either <a href="/request/apiwrite">obtain write keys</a> and use the{' '}
          <a href="/eventwizard2">Event Wizard</a> to input the reports, or post
          them in our{' '}
          <a href="https://www.facebook.com/groups/moardata/">
            Facebook Group.
          </a>
        </p>

        <h2>Other</h2>
        <p>
          For other data you&apos;d like to add, reach out on our{' '}
          <a href="https://www.facebook.com/groups/moardata/">Facebook Group</a>{' '}
          or <Link to="/contact">contact us</Link>, we&apos;ll be happy to help!
        </p>
      </div>
    </div>
  );
}
