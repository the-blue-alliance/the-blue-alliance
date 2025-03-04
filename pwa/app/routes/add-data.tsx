import { Link } from '@remix-run/react';

export default function Add_Data(): React.JSX.Element {
  return (
    <>
      <div className="flex flex-col divide-y **:mt-4">
        <div>
          <h1 className="text-3xl font-medium">Add Data to TBA!</h1>
          <p>
            Do you have some data you&apos;d like to add to The Blue Alliance?
            This page will provide you with the resources you need to help
            contribute to TBA.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Adding Match Videos</h3>
          <p>
            If you have links to YouTube recordings of match video, you can link
            them on TBA. You can suggest videos individually from the detail
            page for a given match, and if you have a YouTube playlist for an
            event, click the &quot;Add Match Videos!&quot; button on the
            &quot;Event&quot; page and input the playlist link. If you&apos;re
            webcasting and archiving an event and want to directly add videos as
            they get uploaded, you can{' '}
            <Link to="/request/apiwrite">request write keys.</Link>
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Event Webcasts</h3>
          <p>
            If you have the link to the webcast for an event, you can suggest it
            from the event&apos;s detail page, or from The Blue Alliance
            homepage if the event is currently active. We make an effort to
            support many stream types, but Twitch.tv, Livestream, and YouTube
            are most common.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Team Media</h3>
          <p>
            You can suggest various types of team media to TBA from a
            team&apos;s detail page in a specific year. You can suggest robot
            pictures, reveal videos, and robot CAD. Team social media accounts,
            like Twitter, Facebook, Instagram, GitHub, and GitLab are not
            year-specific, and persist from year to year.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Adding a New Offseason Event</h3>
          <p>
            Do you know of an offseason event missing from TBA? You can suggest
            an event to be added <Link to="/suggest/offseason">here</Link>. The
            request will be reviewed and added shortly.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Adding Offseason Event Results</h3>
          <h4 className="text-xl">FMS Sync</h4>
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
          <h4 className="text-xl">Offline FMS</h4>
          <p>
            If your offseason event does <em>not</em> have FMS Sync back to
            Headquarters, that&apos;s not an issue either. You can{' '}
            <Link to="/request/apiwrite">request write keys</Link> and post
            individual data points during an event using the{' '}
            <Link to="/eventwizard2">Event Wizard</Link> to get results in a
            timely manner.
          </p>
          <p>
            Alternately, get the FMS Reports exported before you tear down your
            field. TBA can take the Excel files and import them to get match
            data after the fact, to get as much historical data as possible.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">FMS Reports</h3>
          <p>
            We can also import FMS Report exports into The Blue Alliance. You
            can either <Link to="/request/apiwrite">obtain write keys</Link> and
            use the <Link to="/eventwizard2">Event Wizard</Link> to input the
            reports, or post them in our{' '}
            <a href="https://www.facebook.com/groups/moardata/">
              Facebook Group.
            </a>
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Other</h3>
          <p>
            For other data you&apos;d like to add, reach out on our{' '}
            <a href="https://www.facebook.com/groups/moardata/">
              Facebook Group
            </a>{' '}
            or <Link to="/contact">contact us</Link>, we&apos;ll be happy to
            help!
          </p>
        </div>
      </div>
    </>
  );
}
