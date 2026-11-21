import type { JSX } from 'react';

export default function MatchVideoGuidelines(): JSX.Element {
  return (
    <ul className="list-disc space-y-1 pl-6 text-sm text-muted-foreground">
      <li>Your suggestion will be reviewed by a moderator.</li>
      <li>
        Please do not submit match videos from an official <i>FIRST</i> webcast.
      </li>
      <li>
        Videos posted on and linked to an official <i>FIRST</i> channel are
        fine.
      </li>
      <li>
        If you can, include the match preview or the score screen in your video.
        It helps our moderators.
      </li>
    </ul>
  );
}
