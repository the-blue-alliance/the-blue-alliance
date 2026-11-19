import { cn } from 'cn';
import type { CSSProperties, ReactNode, SVGProps } from 'react';

import type { EventColors } from '~/api/colors';
import type {
  NexusMapArrow,
  NexusMapElement,
  NexusMapPit,
  NexusPitMap as NexusPitMapData,
} from '~/api/tba/read';
import { TeamLink } from '~/components/tba/links';
import { parseColor, wcagContrast } from '~/lib/colorContrast';
import { removeNonNumeric } from '~/lib/utils';

function bounds({ position, size, angle }: NexusMapElement) {
  const width = size?.x ?? 0;
  const height = size?.y ?? 0;
  const centerX = position?.x ?? 0;
  const centerY = position?.y ?? 0;
  return {
    rect: { x: centerX - width / 2, y: centerY - height / 2, width, height },
    transform: angle ? `rotate(${angle} ${centerX} ${centerY})` : undefined,
  };
}

function ElementRect({
  element,
  ...props
}: { element: NexusMapElement } & SVGProps<SVGRectElement>) {
  const { rect, transform } = bounds(element);
  return <rect {...rect} transform={transform} {...props} />;
}

function TextBox({
  element,
  className,
  style,
  children,
}: {
  element: NexusMapElement;
  className?: string;
  style?: CSSProperties;
  children: ReactNode;
}) {
  const { rect, transform } = bounds(element);
  return (
    <foreignObject {...rect} transform={transform} className="overflow-visible">
      <div
        className={cn(
          `flex size-full flex-col items-center justify-center text-center
          leading-tight`,
          className,
        )}
        style={{ fontSize: Math.min(rect.width, rect.height) * 0.2, ...style }}
      >
        {children}
      </div>
    </foreignObject>
  );
}

const SINGLE_ARROW = [
  [0.5, 0.12],
  [0.78, 0.45],
  [0.62, 0.45],
  [0.62, 0.88],
  [0.38, 0.88],
  [0.38, 0.45],
  [0.22, 0.45],
];

const DOUBLE_ARROW = [
  [0.5, 0.12],
  [0.78, 0.3],
  [0.62, 0.3],
  [0.62, 0.7],
  [0.78, 0.7],
  [0.5, 0.88],
  [0.22, 0.7],
  [0.38, 0.7],
  [0.38, 0.3],
  [0.22, 0.3],
];

function Arrow({ arrow }: { arrow: NexusMapArrow }) {
  const { rect, transform } = bounds(arrow);
  const shape = arrow.type === 'double' ? DOUBLE_ARROW : SINGLE_ARROW;
  return (
    <polygon
      points={shape
        .map(
          ([x, y]) => `${rect.x + rect.width * x},${rect.y + rect.height * y}`,
        )
        .join(' ')}
      transform={transform}
      className="fill-muted-foreground"
    />
  );
}

function Pit({
  id,
  pit,
  team,
  year,
  colors,
}: {
  id: string;
  pit: NexusMapPit;
  team?: string;
  year: number;
  colors?: EventColors;
}) {
  const hex = team && colors?.teams[removeNonNumeric(team)]?.colors?.primaryHex;
  const fill = hex ? parseColor(hex) : null;
  const text = fill
    ? wcagContrast(fill, '#000000') >= wcagContrast(fill, '#ffffff')
      ? '#000000'
      : '#ffffff'
    : undefined;
  return (
    <g>
      <ElementRect
        element={pit}
        vectorEffect="non-scaling-stroke"
        className="fill-card stroke-muted-foreground/40"
        style={fill ? { fill } : undefined}
      />
      <TextBox element={pit} style={text ? { color: text } : undefined}>
        {team && (
          <TeamLink
            teamOrKey={team}
            year={year}
            className="text-[1.6em] font-bold text-inherit tabular-nums
              hover:underline"
          >
            {team}
          </TeamLink>
        )}
        <span
          className={cn(
            'text-[1.1em] font-medium',
            text ? 'opacity-75' : 'text-muted-foreground',
          )}
        >
          {id}
        </span>
      </TextBox>
    </g>
  );
}

export default function NexusPitMap({
  pitMap,
  year,
  teamsByPit,
  colors,
}: {
  pitMap: NexusPitMapData;
  year: number;
  teamsByPit?: ReadonlyMap<string, string>;
  colors?: EventColors;
}) {
  return (
    <svg
      role="group"
      aria-label="Pit map"
      viewBox={`0 0 ${pitMap.size.x ?? 0} ${pitMap.size.y ?? 0}`}
      className="mx-auto h-auto w-full"
      style={{
        minWidth: (pitMap.size.x ?? 0) * 0.35,
        maxWidth: (pitMap.size.x ?? 0) * 0.6,
      }}
    >
      <g className="fill-muted-foreground opacity-50">
        {Object.entries(pitMap.walls).map(([id, wall]) => (
          <ElementRect key={id} element={wall} />
        ))}
      </g>
      {Object.entries(pitMap.areas).map(([id, area]) => (
        <g key={id}>
          <ElementRect
            element={area}
            rx={8}
            vectorEffect="non-scaling-stroke"
            className="fill-muted stroke-border"
          />
          <TextBox element={area} className="font-medium text-muted-foreground">
            {area.label}
          </TextBox>
        </g>
      ))}
      {Object.entries(pitMap.pits).map(([id, pit]) => (
        <Pit
          key={id}
          id={id}
          pit={pit}
          team={pit.team_key?.slice(3).toUpperCase() ?? teamsByPit?.get(id)}
          year={year}
          colors={colors}
        />
      ))}
      {Object.entries(pitMap.labels).map(([id, label]) => (
        <TextBox key={id} element={label} className="font-medium">
          {label.label}
        </TextBox>
      ))}
      {Object.entries(pitMap.arrows).map(([id, arrow]) => (
        <Arrow key={id} arrow={arrow} />
      ))}
    </svg>
  );
}
