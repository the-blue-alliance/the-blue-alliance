import { type JSX } from 'react';

interface GuidelineSet {
  title: string;
  dos: string[];
  donts: string[];
}

// Approval guidance carried over from the web review templates in
// backend/web/templates/suggestions/. Types without guidance there have none.
export const REVIEW_GUIDELINES: Record<string, GuidelineSet[]> = {
  media: [
    {
      title: 'Video Approval Guidelines',
      dos: [
        "Chairman's video",
        'Robot reveal',
        'Robot testing',
        'Awards ceremony',
        'Practice matches',
      ],
      donts: [
        'Full matches (from any PoV)',
        'People dancing',
        'Long, drawn out videos with little to no real content',
      ],
    },
    {
      title: 'Image Approval Guidelines',
      dos: ['Robot photos', 'Team photos with robot'],
      donts: ['GIFs', 'Images without robot'],
    },
  ],
  event_media: [
    {
      title: 'Approval Guidelines',
      dos: [
        'Videos of award ceremonies',
        'Opening/Closing ceremony speeches',
        'Fun/engaging content created by the community (interviews, interactions, etc.)',
      ],
      donts: [
        'Full matches (from any PoV)',
        'People dancing',
        'Long, drawn out videos with little to no real content',
      ],
    },
  ],
  'offseason-event': [
    {
      title: 'Event Approval Guidelines',
      dos: ["New Offseason Events (ensure they don't already exist)"],
      donts: [
        'Official Events',
        'Events Without Websites you can verify the info for',
      ],
    },
  ],
  api_auth_access: [
    {
      title: 'Request Approval Guidelines',
      dos: ['New requests for events (try to limit one set of keys per event)'],
      donts: [
        'Requests for official events',
        'Requests for events that already have keys issued',
      ],
    },
  ],
};

// "Webcast Formatting Protips" from
// suggestions/partials/webcast_add_instructions_partial.html. Segments marked
// as code render in the global <code> chip style.
type ProtipSegment = string | { code: string };
export const WEBCAST_PROTIPS: { site: string; tip: ProtipSegment[] }[] = [
  {
    site: 'Livestream',
    tip: [
      'URLs are like ',
      { code: 'http://new.livestream.com/nefirst/BeantownBlitz2014' },
      '. Inspect the HTML, find the embed widget, look for ',
      { code: 'account=7031031&event=3138794' },
      '. The "Channel" is the account ID, and the "File" is the event ID.',
    ],
  },
  {
    site: 'Ustream',
    tip: [
      'URLs are like ',
      { code: 'http://www.ustream.tv/channel/nasa-media-channel' },
      '. Click "Embed," look for ',
      { code: 'http://www.ustream.tv/embed/10414700' },
      '. The "Channel" in this case is 10414700.',
    ],
  },
  {
    site: 'DaCast',
    tip: [
      'Inspect the HTML and look for a tag like ',
      {
        code: '<script id="66716_c_219330" src="//player.dacast.com/js/dacast_player.js" class="dacast-video"></script>',
      },
      '. In the "id" attribute, the first number is the "Channel" and the second (after ',
      { code: '_c_' },
      ') is the "File".',
    ],
  },
];

function WebcastProtips(): JSX.Element {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-lg font-medium">Webcast Formatting Protips</h2>
      <div className="rounded-lg border bg-muted/50 p-3 text-sm">
        <dl className="flex flex-col gap-2">
          {WEBCAST_PROTIPS.map(({ site, tip }) => (
            <div key={site}>
              <dt className="font-semibold">{site}</dt>
              <dd className="break-words text-muted-foreground">
                {tip.map((segment, i) =>
                  typeof segment === 'string' ? (
                    segment
                  ) : (
                    <code key={i} className="break-all">
                      {segment.code}
                    </code>
                  ),
                )}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

export function ReviewGuidelines({
  suggestionType,
}: {
  suggestionType: string;
}): JSX.Element | null {
  const sets = REVIEW_GUIDELINES[suggestionType];
  if (suggestionType === 'event') {
    return <WebcastProtips />;
  }
  if (!sets) return null;
  return (
    <div className="flex flex-col gap-3">
      {sets.map((set) => (
        <section key={set.title} className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">{set.title}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div
              className="rounded-lg border border-green-600 bg-green-600/10 p-3
                text-sm"
            >
              <span className="font-semibold">Do approve:</span>
              <ul className="mt-1 list-inside list-disc">
                {set.dos.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div
              className="rounded-lg border border-destructive bg-destructive/10
                p-3 text-sm"
            >
              <span className="font-semibold">Do NOT approve:</span>
              <ul className="mt-1 list-inside list-disc">
                {set.donts.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      ))}
    </div>
  );
}
