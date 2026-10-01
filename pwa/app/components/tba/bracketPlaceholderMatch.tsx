import { cn } from 'cn';
import {
  type Dispatch,
  type JSX,
  type RefObject,
  type SetStateAction,
} from 'react';

import { EliminationAlliance, Event } from '~/api/tba/read';
import { TeamLinkWithTooltip } from '~/components/tba/teamTooltip';
import { Badge } from '~/components/ui/badge';
import {
  type BracketSide,
  type BracketSides,
  sideAllianceNumber,
} from '~/lib/doubleElimBracket';

interface BracketPlaceholderMatchProps {
  matchLabel: string;
  sides: BracketSides;
  alliances: EliminationAlliance[];
  event: Event;
  hoveredAlliance: number | null;
  setHoveredAlliance: Dispatch<SetStateAction<number | null>>;
  getAllianceDisplayName: (allianceNumber: number) => string;
  cardRef: RefObject<HTMLFieldSetElement | null>;
  redRowRef: RefObject<HTMLDivElement | null>;
  blueRowRef: RefObject<HTMLDivElement | null>;
  isNext: boolean;
}

export default function BracketPlaceholderMatch({
  matchLabel,
  sides,
  alliances,
  event,
  hoveredAlliance,
  setHoveredAlliance,
  getAllianceDisplayName,
  cardRef,
  redRowRef,
  blueRowRef,
  isNext,
}: BracketPlaceholderMatchProps): JSX.Element {
  const redAlliance = sideAllianceNumber(sides.red);
  const blueAlliance = sideAllianceNumber(sides.blue);
  const displayName = (allianceNumber: number | null) =>
    allianceNumber ? getAllianceDisplayName(allianceNumber) : 'TBD';

  return (
    <fieldset
      ref={cardRef}
      aria-label={matchLabel}
      className="mb-2 min-w-45 overflow-hidden rounded-md border border-dashed
        border-neutral-300 bg-background dark:border-neutral-600"
    >
      <div
        className="flex items-center justify-between gap-2 border-b
          border-dashed px-2 py-1 text-sm font-bold"
      >
        <div className="flex items-center gap-1">
          <span>{matchLabel}</span>
          {(redAlliance || blueAlliance) && (
            <span className="text-xs font-normal">
              ({displayName(redAlliance)} vs {displayName(blueAlliance)})
            </span>
          )}
        </div>
        {isNext && <Badge variant="success">Next</Badge>}
      </div>
      <PlaceholderRow
        side={sides.red}
        rowRef={redRowRef}
        className="bg-alliance-red-loser"
        alliances={alliances}
        event={event}
        hoveredAlliance={hoveredAlliance}
        setHoveredAlliance={setHoveredAlliance}
      />
      <PlaceholderRow
        side={sides.blue}
        rowRef={blueRowRef}
        className="bg-alliance-blue-loser"
        alliances={alliances}
        event={event}
        hoveredAlliance={hoveredAlliance}
        setHoveredAlliance={setHoveredAlliance}
      />
    </fieldset>
  );
}

function PlaceholderRow({
  side,
  rowRef,
  className,
  alliances,
  event,
  hoveredAlliance,
  setHoveredAlliance,
}: {
  side: BracketSide;
  rowRef: RefObject<HTMLDivElement | null>;
  className: string;
  alliances: EliminationAlliance[];
  event: Event;
  hoveredAlliance: number | null;
  setHoveredAlliance: Dispatch<SetStateAction<number | null>>;
}): JSX.Element {
  const allianceNumber = sideAllianceNumber(side);
  const picks = allianceNumber ? alliances[allianceNumber - 1]?.picks : null;

  return (
    <div
      ref={rowRef}
      className={cn(
        `flex min-h-7 items-center px-1 py-1 transition-colors duration-200
        data-[highlight=true]:ring-2 data-[highlight=true]:ring-foreground
        data-[highlight=true]:ring-inset`,
        allianceNumber && 'cursor-pointer',
        className,
      )}
      data-highlight={
        allianceNumber !== null && hoveredAlliance === allianceNumber
      }
      onMouseEnter={() => allianceNumber && setHoveredAlliance(allianceNumber)}
      onMouseLeave={() => allianceNumber && setHoveredAlliance(null)}
    >
      {picks ? (
        picks.map((teamKey) => (
          <span key={teamKey} className="w-12 text-center text-sm">
            <TeamLinkWithTooltip
              className="text-inherit"
              teamKey={teamKey}
              year={event.year}
            />
          </span>
        ))
      ) : (
        <span className="px-1 text-sm text-muted-foreground italic">
          {'placeholder' in side ? side.placeholder : 'TBD'}
        </span>
      )}
    </div>
  );
}
