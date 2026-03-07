import {
  type JSX,
  type MutableRefObject,
  type RefObject,
  useEffect,
  useState,
} from 'react';

import { Match } from '~/api/tba/read';

type MatchResult = {
  score: number;
  won: boolean;
};

export interface SeriesResult {
  redTeams: string[];
  blueTeams: string[];
  redAllianceNumber: number | null;
  blueAllianceNumber: number | null;
  redResults: MatchResult[];
  blueResults: MatchResult[];
  redWon: boolean;
  blueWon: boolean;
  matchRedTeams: string[];
  matchBlueTeams: string[];
}

export type WinnerLink = { from: string; to: string };

export type PlayoffMatchHandle = {
  card: HTMLDivElement | null;
  redRow: HTMLDivElement | null;
  blueRow: HTMLDivElement | null;
  redAlliance: number | null;
  blueAlliance: number | null;
};

export type AdvancementPath = {
  d: string;
  winner: 'red' | 'blue';
  allianceNumber: number | null;
  key: string;
};

const saturatedColors = {
  red: 'var(--color-red-500)',
  blue: 'var(--color-blue-500)',
};
const desaturatedColors = {
  red: 'var(--color-red-300)',
  blue: 'var(--color-blue-300)',
};

export function useAdvancementPaths({
  containerRef,
  matchRefs,
  winnerLinks,
  matchLookup,
  getSeriesResult,
}: {
  containerRef: RefObject<HTMLDivElement | null>;
  matchRefs: MutableRefObject<Record<string, PlayoffMatchHandle | null>>;
  winnerLinks: WinnerLink[];
  matchLookup: Record<string, Match[] | undefined>;
  getSeriesResult: (matches: Match[] | undefined) => SeriesResult | null;
}): { paths: AdvancementPath[]; svgSize: { width: number; height: number } } {
  const [paths, setPaths] = useState<AdvancementPath[]>([]);
  const [svgSize, setSvgSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const computePaths = () => {
      if (!containerRef.current) {
        setPaths([]);
        return;
      }
      const containerRect = containerRef.current.getBoundingClientRect();
      const nextPaths: AdvancementPath[] = [];

      winnerLinks.forEach((link) => {
        const fromNode = matchRefs.current[link.from];
        const toNode = matchRefs.current[link.to];
        if (!fromNode || !toNode) return;

        const seriesResult = getSeriesResult(matchLookup[link.from]);
        if (!seriesResult) return;
        let winner: 'red' | 'blue' | null = null;
        let allianceNumber: number | null = null;
        if (seriesResult.redWon && seriesResult.redAllianceNumber) {
          winner = 'red';
          allianceNumber = seriesResult.redAllianceNumber;
        } else if (seriesResult.blueWon && seriesResult.blueAllianceNumber) {
          winner = 'blue';
          allianceNumber = seriesResult.blueAllianceNumber;
        }
        if (!winner) return;

        const fromRow = winner === 'red' ? fromNode.redRow : fromNode.blueRow;
        const fromRect = (fromRow ?? fromNode.card)?.getBoundingClientRect();
        if (!fromRect) return;

        let toRow: HTMLDivElement | null = null;
        if (allianceNumber && toNode.redAlliance === allianceNumber) {
          toRow = toNode.redRow;
        } else if (allianceNumber && toNode.blueAlliance === allianceNumber) {
          toRow = toNode.blueRow;
        }
        const toRect = (toRow ?? toNode.card)?.getBoundingClientRect();
        if (!toRect) return;

        const startX = fromRect.right - containerRect.left;
        const startY = (fromRect.top + fromRect.bottom) / 2 - containerRect.top;
        const endX = toRect.left - containerRect.left;
        const endY = (toRect.top + toRect.bottom) / 2 - containerRect.top;
        const control1X = startX + 32;
        const control2X = endX - 32;

        const d = `M ${startX} ${startY} C ${control1X} ${startY} ${control2X} ${endY} ${endX} ${endY}`;
        nextPaths.push({
          d,
          winner,
          allianceNumber,
          key: `${link.from}-${link.to}`,
        });
      });

      setPaths(nextPaths);
      setSvgSize({
        width: containerRect.width,
        height: containerRect.height,
      });
    };

    const handle = () => window.requestAnimationFrame(computePaths);
    handle();
    window.addEventListener('resize', handle);
    return () => window.removeEventListener('resize', handle);
  }, [containerRef, matchRefs, winnerLinks, matchLookup, getSeriesResult]);

  return { paths, svgSize };
}

export function EliminationBracketPaths({
  paths,
  svgSize,
  hoveredAlliance,
}: {
  paths: AdvancementPath[];
  svgSize: { width: number; height: number };
  hoveredAlliance: number | null;
}): JSX.Element | null {
  if (svgSize.width === 0 || svgSize.height === 0) {
    return null;
  }

  return (
    <svg
      className="pointer-events-none absolute inset-0"
      width={svgSize.width}
      height={svgSize.height}
      viewBox={`0 0 ${svgSize.width} ${svgSize.height}`}
    >
      {paths.map((path) => {
        const isHovered =
          hoveredAlliance !== null && path.allianceNumber === hoveredAlliance;
        const stroke = isHovered
          ? saturatedColors[path.winner]
          : desaturatedColors[path.winner];
        return (
          <path
            key={path.key}
            d={path.d}
            stroke={stroke}
            strokeWidth={isHovered ? 4 : 3}
            strokeOpacity={isHovered ? 1 : 0.6}
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              filter: isHovered
                ? 'drop-shadow(0 0 8px rgba(0, 0, 0, 0.35))'
                : 'none',
              transition:
                'stroke 200ms ease, stroke-width 200ms ease, stroke-opacity 200ms ease, filter 200ms ease',
            }}
          />
        );
      })}
    </svg>
  );
}
