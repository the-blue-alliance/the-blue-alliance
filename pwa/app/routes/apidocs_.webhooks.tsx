import { Link, createFileRoute } from '@tanstack/react-router';
import { type ReactNode, useState } from 'react';

import WebhookTestForm from '~/components/tba/apidocs/webhookTestForm';
import {
  TableOfContents,
  TableOfContentsSection,
} from '~/components/tba/tableOfContents';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '~/components/ui/table';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/apidocs_/webhooks')({
  headers: publicCacheControlHeaders(),
  component: WebhookDocs,
  head: () => ({
    meta: [
      { title: 'Webhooks - The Blue Alliance' },
      {
        name: 'description',
        content: "Documentation for The Blue Alliance's webhook API.",
      },
    ],
  }),
}); // v8 ignore start -- TanStack Router's dev-only HMR code maps to this line
// v8 ignore stop

interface Field {
  key: string;
  description: ReactNode;
  example?: string;
}

interface NotificationDoc {
  slug: string;
  title: string;
  messageType: string;
  description: ReactNode;
  fields: Field[];
  example: object;
  test?: { eventKey?: string; matchKey?: string };
}

const Optional = () => <strong>Optional.</strong>;

const eventKeyField: Field = {
  key: 'event_key',
  description: 'The key of the event',
  example: '2014necmp',
};

const matchKeyField: Field = {
  key: 'match_key',
  description: 'The key of the match',
  example: '2014necmp_f1m1',
};

const teamKeyField: Field = {
  key: 'team_key',
  description: (
    <>
      <Optional /> The key of the team. Only included when the notification is
      sent for a team subscription.
    </>
  ),
  example: 'frc7332',
};

const eventNameField: Field = {
  key: 'event_name',
  description:
    'The official name of the event, from FIRST or the offseason event organizers',
  example: 'New England FRC Region Championship',
};

const modelField = (key: string, model: string, extra = ''): Field => ({
  key,
  description: (
    <>
      A <Link to="/apidocs/v3">Read API</Link> {model} object{extra}
    </>
  ),
});

const scoredMatch = {
  comp_level: 'f',
  match_number: 1,
  videos: [],
  time_string: '3:18 PM',
  set_number: 1,
  key: '2014necmp_f1m1',
  time: 1397330280,
  score_breakdown: null,
  alliances: {
    blue: { score: 154, teams: ['frc177', 'frc230', 'frc4055'] },
    red: { score: 78, teams: ['frc195', 'frc558', 'frc5122'] },
  },
  event_key: '2014necmp',
};

const notifications: NotificationDoc[] = [
  {
    slug: 'upcoming_match',
    title: 'Upcoming Match',
    messageType: 'upcoming_match',
    description: (
      <>
        Sent after scores are posted for match N - 2. When a match schedule is
        first released, or for the first match of a new day, it is sent about 7
        minutes before the match starts.
      </>
    ),
    fields: [
      eventKeyField,
      matchKeyField,
      teamKeyField,
      eventNameField,
      {
        key: 'team_keys',
        description: 'The keys of all teams in the match',
        example: 'frc195, frc558, ...',
      },
      {
        key: 'scheduled_time',
        description: (
          <>
            <Optional /> The time the match was first scheduled for, in Unix
            UTC. Left out if the match has no scheduled time.
          </>
        ),
        example: '1397330280',
      },
      {
        key: 'predicted_time',
        description: (
          <>
            <Optional /> The time the match is predicted to start, in Unix UTC,
            based on when earlier scores were posted. Left out if no prediction
            is possible.
          </>
        ),
        example: '1397330280',
      },
      modelField(
        'webcast',
        'Webcast',
        '. Optional. One online webcast for the event, even if the event has more. Left out if no webcast is online.',
      ),
    ],
    example: {
      message_data: {
        event_key: '2014necmp',
        match_key: '2014necmp_f1m1',
        event_name: 'New England FRC Region Championship',
        team_keys: [
          'frc195',
          'frc558',
          'frc5122',
          'frc177',
          'frc230',
          'frc4055',
        ],
        scheduled_time: 1397330280,
        predicted_time: 1397330280,
        webcast: { type: 'twitch', channel: 'nefirst_blue' },
      },
      message_type: 'upcoming_match',
    },
    test: { matchKey: '2014necmp_f1m1' },
  },
  {
    slug: 'match_score',
    title: 'Match Score',
    messageType: 'match_score',
    description: 'Sent every time a match score at a live event is updated.',
    fields: [
      eventKeyField,
      matchKeyField,
      teamKeyField,
      eventNameField,
      modelField('match', 'Match'),
    ],
    example: {
      message_data: {
        event_name: 'New England FRC Region Championship',
        match: scoredMatch,
      },
      message_type: 'match_score',
    },
    test: { matchKey: '2014necmp_f1m1' },
  },
  {
    slug: 'match_video',
    title: 'Match Video',
    messageType: 'match_video',
    description: 'Sent every time a video is added to a match.',
    fields: [
      eventKeyField,
      matchKeyField,
      teamKeyField,
      eventNameField,
      modelField('match', 'Match'),
    ],
    example: {
      message_data: {
        event_name: 'New England FRC Region Championship',
        match: {
          comp_level: 'f',
          match_number: 1,
          videos: [{ key: 'ZrDxXDC1y5I', type: 'youtube' }],
          time_string: '3:18 PM',
          set_number: 1,
          key: '2014necmp_f1m1',
          time: 1397330280,
          score_breakdown: null,
          event_key: '2014necmp',
        },
      },
      message_type: 'match_video',
    },
    test: { matchKey: '2014necmp_f1m1' },
  },
  {
    slug: 'level_starting',
    title: 'Competition Level Starting',
    messageType: 'starting_comp_level',
    description: (
      <>
        Sent with <a href="#upcoming_match">Upcoming Match notifications</a>{' '}
        when the next match is in a new competition level, such as the first
        semifinal.
      </>
    ),
    fields: [
      eventKeyField,
      eventNameField,
      {
        key: 'comp_level',
        description: (
          <>
            The competition level that is starting. One of{' '}
            <a href="https://github.com/the-blue-alliance/the-blue-alliance/blob/main/src/backend/common/consts/comp_level.py">
              these values
            </a>
            .
          </>
        ),
        example: 'qf',
      },
      {
        key: 'scheduled_time',
        description: (
          <>
            <Optional /> The time the level&apos;s first match was scheduled
            for, in Unix UTC. Left out if the match has no scheduled time.
          </>
        ),
        example: '1397330280',
      },
    ],
    example: {
      message_data: {
        event_name: 'New England FRC Region Championship',
        comp_level: 'f',
        event_key: '2014necmp',
        scheduled_time: 1397330280,
      },
      message_type: 'starting_comp_level',
    },
    test: { matchKey: '2014necmp_f1m1' },
  },
  {
    slug: 'alliance_selection',
    title: 'Alliance Selection',
    messageType: 'alliance_selection',
    description: "Sent after an event's alliance selection results are posted.",
    fields: [
      eventKeyField,
      teamKeyField,
      eventNameField,
      modelField('event', 'Event'),
    ],
    example: {
      message_data: {
        event_name: 'New England FRC Region Championship',
        event_key: '2014necmp',
        event: {
          address: 'Boston, MA 02215, USA',
          city: 'Boston',
          country: 'USA',
          district: {
            abbreviation: 'ne',
            display_name: 'New England',
            key: '2014ne',
            year: 2014,
          },
          division_keys: [],
          end_date: '2014-04-12',
          event_code: 'necmp',
          event_type: 2,
          event_type_string: 'District Championship',
          first_event_code: 'necmp',
          first_event_id: '10871',
          gmaps_place_id: 'ChIJFzjlY_B544kRyL6j4ABuNCs',
          gmaps_url: 'https://maps.google.com/?cid=3113234192467738312',
          key: '2014necmp',
          lat: 42.3504997,
          lng: -71.1053991,
          location_name: 'Boston University',
          name: 'New England FRC Region Championship',
          parent_event_key: null,
          playoff_type: null,
          playoff_type_string: null,
          postal_code: '02215',
          short_name: 'New England',
          start_date: '2014-04-10',
          state_prov: 'MA',
          timezone: 'America/New_York',
          webcasts: [
            { channel: '7031031', file: '2797186', type: 'livestream' },
            { channel: '7234441', file: '2797207', type: 'livestream' },
          ],
          website: 'http://www.nefirst.org/',
          week: 6,
          year: 2014,
        },
      },
      message_type: 'alliance_selection',
    },
    test: { eventKey: '2014necmp' },
  },
  {
    slug: 'awards',
    title: 'Awards Posted',
    messageType: 'awards_posted',
    description: 'Sent every time an award is added at a live event.',
    fields: [
      eventKeyField,
      teamKeyField,
      eventNameField,
      modelField(
        'awards',
        'Award',
        's list. For an event subscription, this has every award at the event. For a team subscription, it has only the awards the team won.',
      ),
    ],
    example: {
      message_data: {
        event_key: '2014necmp',
        event_name: 'New England FRC Region Championship',
        awards: [
          {
            event_key: '2014necmp',
            award_type: 0,
            name: "Regional Chairman's Award",
            recipient_list: [
              { team_number: 2067, awardee: null },
              { team_number: 78, awardee: null },
              { team_number: 811, awardee: null },
              { team_number: 2648, awardee: null },
            ],
            year: 2014,
          },
        ],
      },
      message_type: 'awards_posted',
    },
    test: { eventKey: '2014necmp' },
  },
  {
    slug: 'schedule_updated',
    title: 'Event Schedule Updated',
    messageType: 'schedule_updated',
    description: 'Sent when new unplayed matches are added to a live event.',
    fields: [
      eventKeyField,
      eventNameField,
      {
        key: 'first_match_time',
        description: (
          <>
            <Optional /> The scheduled time of the next unplayed match, in Unix
            UTC. Left out if the match has no scheduled time.
          </>
        ),
        example: '1397330280',
      },
    ],
    example: {
      message_data: {
        event_key: '2014necmp',
        event_name: 'New England FRC Region Championship',
        first_match_time: 1397330280,
      },
      message_type: 'schedule_updated',
    },
    test: { eventKey: '2014necmp', matchKey: '2014necmp_f1m1' },
  },
  {
    slug: 'ping',
    title: 'Ping',
    messageType: 'ping',
    description: (
      <>
        Sent when you press Ping for a webhook on your{' '}
        <Link to="/account">account page</Link>.
      </>
    ),
    fields: [
      { key: 'title', description: 'The title', example: 'Test Message' },
      {
        key: 'desc',
        description: 'The message',
        example:
          'This is a test message ensuring your device can recieve push messages from The Blue Alliance.',
      },
    ],
    example: {
      message_data: {
        title: 'Test Message',
        desc: 'This is a test message ensuring your device can recieve push messages from The Blue Alliance.',
      },
      message_type: 'ping',
    },
  },
  {
    slug: 'broadcast',
    title: 'Broadcast',
    messageType: 'broadcast',
    description: 'Sent by TBA admins to announce something important.',
    fields: [
      {
        key: 'title',
        description: 'The title of the notification',
        example: 'Test',
      },
      {
        key: 'desc',
        description: 'The text of the notification',
        example: 'Test Broadcast',
      },
      {
        key: 'url',
        description: (
          <>
            <Optional /> A URL with more information
          </>
        ),
        example: 'http://foo.bar',
      },
    ],
    example: {
      message_data: {
        title: 'Test',
        desc: 'Test Broadcast',
        url: 'http://foo.bar',
      },
      message_type: 'broadcast',
    },
  },
  {
    slug: 'verification',
    title: 'Verification',
    messageType: 'verification',
    description: (
      <>
        Sent when you add a webhook or ask for a new code. Enter the code for
        the webhook on your <Link to="/account">account page</Link> before it
        can get live updates.
      </>
    ),
    fields: [
      {
        key: 'verification_key',
        description: 'The verification code for the webhook',
        example: '8279a61abdeee0cf46a86136bf888188a4b18cdf',
      },
    ],
    example: {
      message_data: {
        verification_key: '8279a61abdeee0cf46a86136bf888188a4b18cdf',
      },
      message_type: 'verification',
    },
  },
];

const tocItems = [
  { slug: 'overview', label: 'Overview' },
  { slug: 'request', label: 'Request Structure' },
  {
    slug: 'configuration',
    label: 'Configuration',
    children: [
      { slug: 'validation', label: 'Verification' },
      { slug: 'testing', label: 'Testing' },
      { slug: 'firehose', label: 'The Firehose' },
    ],
  },
  {
    slug: 'notifications',
    label: 'Notification Types',
    children: notifications.map(({ slug, title }) => ({ slug, label: title })),
  },
];

function WebhookDocs() {
  const [inView, setInView] = useState(new Set<string>());

  return (
    <div className="flex flex-wrap gap-8 lg:flex-nowrap">
      <TableOfContents tocItems={tocItems} inView={inView} />
      <div className="min-w-0 basis-full space-y-2 md:basis-5/6">
        <h1 className="mb-2 text-3xl font-medium">Webhooks</h1>

        <TableOfContentsSection
          id="overview"
          setInView={setInView}
          className="py-4"
        >
          <h2 className="mb-2 text-2xl font-medium">Overview</h2>
          <p>
            Webhooks let The Blue Alliance push notifications to your server
            when data changes. Each notification is an HTTP POST request to a
            URL you choose. Webhooks do not replace the{' '}
            <Link to="/apidocs">API</Link>. Use them instead of polling the API
            often, or anywhere you need updates in real time.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="request"
          setInView={setInView}
          className="space-y-2 py-4"
        >
          <h2 className="mb-2 text-2xl font-medium">Request Structure</h2>
          <p>
            Each request has a JSON body with two fields.{' '}
            <code>message_type</code> tells you what kind of notification it is.{' '}
            <code>message_data</code> holds the data for that type. Each type is
            described <a href="#notifications">below</a>.
          </p>
          <p>
            Each request also has an <code>X-TBA-HMAC</code> header, so you can
            check that the request came from TBA. It is an{' '}
            <a href="https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.198-1.pdf">
              HMAC
            </a>{' '}
            of the request body, using SHA256 and your webhook&apos;s secret as
            the key. You can see{' '}
            <a href="https://github.com/the-blue-alliance/the-blue-alliance/blob/main/src/backend/common/models/notifications/requests/webhook_request.py">
              how it is calculated in our code
            </a>
            .
          </p>
          <p>
            TBA waits 10 seconds for your server to respond. A request that
            takes longer counts as failed.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="configuration"
          setInView={setInView}
          className="space-y-2 py-4"
        >
          <h2 className="mb-2 text-2xl font-medium">Configuration</h2>
          <p>
            Webhooks belong to your TBA account. Add them on your{' '}
            <Link to="/account">account page</Link>. Enter a name and the URL
            that should get notifications. TBA makes a secret for each webhook,
            which you use to check the <code>X-TBA-HMAC</code> header. Make sure
            your server is listening for POST requests at that URL. If it does
            not respond, or responds with an error, your webhook may be deleted.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="validation"
          setInView={setInView}
          className="space-y-2 py-4"
        >
          <h3 className="mb-2 text-xl">Verification</h3>
          <p>
            When you add a webhook, TBA sends it a{' '}
            <a href="#verification">verification</a> message, like this:
          </p>
          <JsonExample
            value={{
              message_type: 'verification',
              message_data: {
                verification_key: 'a93774ec6197d456f4aaadfea5fdba6697e71e6a',
              },
            }}
          />
          <p>
            Go to your <Link to="/account">account page</Link> and enter that
            code to verify the webhook. You can ask for a new code there too.
            Only the most recent code works.
          </p>
          <p>
            Until you verify a webhook, it gets no notifications except pings.
            You can ping an unverified webhook from your account page to check
            that it works. Verify your webhooks soon after you add them.
          </p>
          <p>
            From time to time we delete webhooks that do not respond to a ping
            with a 200 status code. Make sure your webhook responds to pings.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="testing"
          setInView={setInView}
          className="space-y-2 py-4"
        >
          <h3 className="mb-2 text-xl">Testing</h3>
          <p>
            To test webhooks on your own computer, you can use{' '}
            <a href="https://ngrok.com/download">ngrok</a> to make a local port
            reachable from the internet. GitHub&apos;s{' '}
            <a href="https://developer.github.com/webhooks/configuring/">
              webhook testing guide
            </a>{' '}
            shows how. There is also a{' '}
            <a href="https://github.com/phil-lopreiato/tba-webhook-test">
              small example script
            </a>
            .
          </p>
          <p>
            Each notification type below that is turned on has a form to send a
            sample notification to one of your verified webhooks. The samples
            use event <code>2014necmp</code> and match{' '}
            <code>2014necmp_f1m1</code> unless you change them.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="firehose"
          setInView={setInView}
          className="space-y-2 py-4"
        >
          <h3 className="mb-2 text-xl">
            <a href="https://tba-notification-firehose.appspot.com/">
              The Firehose
            </a>
          </h3>
          <p>
            To get updates for <em>every</em> event in a year, subscribe to the
            TBA Notification Firehose. On your{' '}
            <Link to="/account/mytba">myTBA page</Link>, subscribe to all events
            this year and choose the notification types you want. The
            subscription lasts for one season, so subscribe again each year.
          </p>
          <p>
            <strong>Warning:</strong> the Firehose also sends every notification
            to every phone signed in to your account. Use an account that is not
            signed in on your phone, unless you want a constant stream of
            notifications there too.
          </p>
          <p>
            See an{' '}
            <a href="https://github.com/the-blue-alliance/the-blue-alliance-notification-firehose">
              example App Engine site
            </a>{' '}
            that subscribes to the Firehose, stores the data, and shows it.
          </p>
        </TableOfContentsSection>

        <TableOfContentsSection
          id="notifications"
          setInView={setInView}
          className="py-4"
        >
          <h2 className="mb-2 text-2xl font-medium">Notification Types</h2>
          <p>
            Not every type is turned on yet. The{' '}
            <code>ENABLED_NOTIFICATIONS</code> list in{' '}
            <a href="https://github.com/the-blue-alliance/the-blue-alliance/blob/main/src/backend/common/consts/notification_type.py">
              this file
            </a>{' '}
            shows which types are on.
          </p>
        </TableOfContentsSection>

        {notifications.map((notification) => (
          <TableOfContentsSection
            key={notification.slug}
            id={notification.slug}
            setInView={setInView}
            className="space-y-3 py-4"
          >
            <NotificationSection notification={notification} />
          </TableOfContentsSection>
        ))}
      </div>
    </div>
  );
}

function NotificationSection({
  notification,
}: {
  notification: NotificationDoc;
}) {
  return (
    <>
      <h3 className="text-xl">{notification.title}</h3>
      <p>{notification.description}</p>
      <p>
        Message type: <code>{notification.messageType}</code>
      </p>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <code>message_data</code> field
            </TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Example</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {notification.fields.map((field) => (
            <TableRow key={field.key}>
              <TableCell className="align-top">
                <code>{field.key}</code>
              </TableCell>
              <TableCell className="align-top whitespace-normal">
                {field.description}
              </TableCell>
              <TableCell className="align-top wrap-anywhere whitespace-normal">
                {field.example}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <JsonExample value={notification.example} />
      {notification.test && (
        <WebhookTestForm
          notificationType={notification.messageType}
          label={notification.title}
          {...notification.test}
        />
      )}
    </>
  );
}

function JsonExample({ value }: { value: object }) {
  return (
    <pre className="overflow-x-auto rounded-md bg-muted p-4 text-xs">
      <code>{JSON.stringify(value, null, 2)}</code>
    </pre>
  );
}
