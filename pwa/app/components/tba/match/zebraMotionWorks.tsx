import { useCallback, useEffect, useRef, useState } from 'react';

import PauseIcon from '~icons/lucide/pause';
import PlayIcon from '~icons/lucide/play';

import type { Zebra } from '~/api/tba/read';
import { Button } from '~/components/ui/button';
import { Slider } from '~/components/ui/slider';

const FIELD_WIDTH_FT = 54;
const FIELD_HEIGHT_FT = 27;
const SVG_WIDTH = 540;
const SVG_HEIGHT = 270;
const ROBOT_RADIUS = 8;

function ftToSvgX(ft: number): number {
  return (ft / FIELD_WIDTH_FT) * SVG_WIDTH;
}

function ftToSvgY(ft: number): number {
  return SVG_HEIGHT - (ft / FIELD_HEIGHT_FT) * SVG_HEIGHT;
}

export default function ZebraMotionWorks({ zebra }: { zebra: Zebra }) {
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const animationRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);

  const totalFrames = zebra.times.length;
  const redTeams = zebra.alliances.red ?? [];
  const blueTeams = zebra.alliances.blue ?? [];

  const animate = useCallback(
    (timestamp: number) => {
      if (lastTimeRef.current === null) {
        lastTimeRef.current = timestamp;
      }

      const elapsed = timestamp - lastTimeRef.current;
      // Zebra data is typically at 10Hz (100ms intervals)
      const frameDuration = 100 / playbackSpeed;

      if (elapsed >= frameDuration) {
        setFrameIndex((prev) => {
          const next = prev + 1;
          if (next >= totalFrames) {
            setIsPlaying(false);
            return prev;
          }
          return next;
        });
        lastTimeRef.current = timestamp;
      }

      animationRef.current = requestAnimationFrame(animate);
    },
    [playbackSpeed, totalFrames],
  );

  useEffect(() => {
    if (isPlaying) {
      lastTimeRef.current = null;
      animationRef.current = requestAnimationFrame(animate);
    } else if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, animate]);

  const togglePlayback = () => {
    if (frameIndex >= totalFrames - 1) {
      setFrameIndex(0);
    }
    setIsPlaying((prev) => !prev);
  };

  const currentTime = zebra.times[frameIndex] ?? 0;
  const duration = zebra.times[totalFrames - 1] ?? 0;

  return (
    <div className="flex flex-col gap-2 rounded-lg border bg-muted/50 p-3">
      <h3 className="text-sm font-semibold">Zebra MotionWorks</h3>
      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="w-full rounded border bg-[#333]"
      >
        {/* Field outline */}
        <rect
          x={0}
          y={0}
          width={SVG_WIDTH}
          height={SVG_HEIGHT}
          fill="none"
          stroke="#666"
          strokeWidth={2}
        />

        {/* Center line */}
        <line
          x1={SVG_WIDTH / 2}
          y1={0}
          x2={SVG_WIDTH / 2}
          y2={SVG_HEIGHT}
          stroke="#555"
          strokeWidth={1}
          strokeDasharray="4 4"
        />

        {/* Alliance zones */}
        <rect
          x={0}
          y={0}
          width={SVG_WIDTH * (10 / FIELD_WIDTH_FT)}
          height={SVG_HEIGHT}
          fill="rgba(239, 68, 68, 0.1)"
          stroke="rgba(239, 68, 68, 0.3)"
          strokeWidth={1}
        />
        <rect
          x={SVG_WIDTH * (44 / FIELD_WIDTH_FT)}
          y={0}
          width={SVG_WIDTH * (10 / FIELD_WIDTH_FT)}
          height={SVG_HEIGHT}
          fill="rgba(59, 130, 246, 0.1)"
          stroke="rgba(59, 130, 246, 0.3)"
          strokeWidth={1}
        />

        {/* Red alliance robots */}
        {redTeams.map((team, i) => {
          const x = team.xs[frameIndex];
          const y = team.ys[frameIndex];
          if (x == null || y == null) return null;
          return (
            <g key={team.team_key}>
              <circle
                cx={ftToSvgX(x)}
                cy={ftToSvgY(y)}
                r={ROBOT_RADIUS}
                fill={`rgba(239, 68, 68, ${0.7 + i * 0.1})`}
                stroke="white"
                strokeWidth={1.5}
              />
              <text
                x={ftToSvgX(x)}
                y={ftToSvgY(y) + 3}
                textAnchor="middle"
                fill="white"
                fontSize={8}
                fontWeight="bold"
              >
                {team.team_key.substring(3)}
              </text>
            </g>
          );
        })}

        {/* Blue alliance robots */}
        {blueTeams.map((team, i) => {
          const x = team.xs[frameIndex];
          const y = team.ys[frameIndex];
          if (x == null || y == null) return null;
          return (
            <g key={team.team_key}>
              <circle
                cx={ftToSvgX(x)}
                cy={ftToSvgY(y)}
                r={ROBOT_RADIUS}
                fill={`rgba(59, 130, 246, ${0.7 + i * 0.1})`}
                stroke="white"
                strokeWidth={1.5}
              />
              <text
                x={ftToSvgX(x)}
                y={ftToSvgY(y) + 3}
                textAnchor="middle"
                fill="white"
                fontSize={8}
                fontWeight="bold"
              >
                {team.team_key.substring(3)}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Playback controls */}
      <div className="flex items-center gap-2">
        <Button size="icon" variant="outline" onClick={togglePlayback}>
          {isPlaying ? (
            <PauseIcon className="size-4" />
          ) : (
            <PlayIcon className="size-4" />
          )}
        </Button>
        <Slider
          value={[frameIndex]}
          max={Math.max(totalFrames - 1, 1)}
          step={1}
          onValueChange={([value]) => {
            setFrameIndex(value);
            if (isPlaying) {
              setIsPlaying(false);
            }
          }}
          className="flex-1"
        />
        <span
          className="min-w-16 text-right text-xs text-muted-foreground
            tabular-nums"
        >
          {currentTime.toFixed(1)}s / {duration.toFixed(1)}s
        </span>
      </div>

      {/* Speed controls */}
      <div className="flex items-center gap-1">
        <span className="text-xs text-muted-foreground">Speed:</span>
        {[0.5, 1, 2, 4].map((speed) => (
          <Button
            key={speed}
            size="sm"
            variant={playbackSpeed === speed ? 'default' : 'outline'}
            onClick={() => setPlaybackSpeed(speed)}
            className="h-6 px-2 text-xs"
          >
            {speed}x
          </Button>
        ))}
      </div>
    </div>
  );
}
