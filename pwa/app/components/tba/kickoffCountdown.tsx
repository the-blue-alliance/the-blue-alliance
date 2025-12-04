import { useEffect, useState } from 'react';

import BiInfoCircleFill from '~icons/bi/info-circle-fill';
import BiPlayFill from '~icons/bi/play-fill';

function calculateTimeRemaining(targetDate: Date): {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  totalMs: number;
} {
  const now = new Date();
  const totalMs = targetDate.getTime() - now.getTime();

  if (totalMs <= 0) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, totalMs: 0 };
  }

  const seconds = Math.floor((totalMs / 1000) % 60);
  const minutes = Math.floor((totalMs / 1000 / 60) % 60);
  const hours = Math.floor((totalMs / (1000 * 60 * 60)) % 24);
  const days = Math.floor(totalMs / (1000 * 60 * 60 * 24));

  return { days, hours, minutes, seconds, totalMs };
}

function formatTimeUnit(value: number): string {
  return value.toString().padStart(2, '0');
}

export function KickoffCountdown({
  kickoffDateTimeEST,
}: {
  kickoffDateTimeEST: Date;
}) {
  const [timeRemaining, setTimeRemaining] = useState(() =>
    calculateTimeRemaining(kickoffDateTimeEST),
  );
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);

    const interval = setInterval(() => {
      const remaining = calculateTimeRemaining(kickoffDateTimeEST);
      setTimeRemaining(remaining);

      if (remaining.totalMs <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [kickoffDateTimeEST]);

  const isKickoffTime = timeRemaining.totalMs <= 0;
  const isWithin24Hours = timeRemaining.totalMs <= 24 * 60 * 60 * 1000;
  const kickoffDate = kickoffDateTimeEST.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
  const kickoffTime = kickoffDateTimeEST.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  });
  const year = kickoffDateTimeEST.getFullYear();

  return (
    <div
      className="mx-auto max-w-[600px] rounded-xl bg-gradient-to-br
        from-slate-100 to-slate-200 p-6 text-slate-800 shadow-lg"
    >
      <h2
        className="mb-4 text-center text-2xl font-bold text-slate-900
          sm:text-3xl"
      >
        Kickoff {year}!
      </h2>

      {isKickoffTime ? (
        <p className="mb-4 text-center text-lg font-medium">
          Kickoff {year} is happening now!
        </p>
      ) : (
        <>
          <div className="mb-4 flex justify-center gap-2 sm:gap-4">
            <CountdownUnit
              value={isClient ? timeRemaining.days : '--'}
              label="D"
              fullLabel="Days"
            />
            <CountdownUnit
              value={isClient ? formatTimeUnit(timeRemaining.hours) : '--'}
              label="H"
              fullLabel="Hours"
            />
            <CountdownUnit
              value={isClient ? formatTimeUnit(timeRemaining.minutes) : '--'}
              label="M"
              fullLabel="Minutes"
            />
            <CountdownUnit
              value={isClient ? formatTimeUnit(timeRemaining.seconds) : '--'}
              label="S"
              fullLabel="Seconds"
            />
          </div>

          <p className="mb-1 text-center text-sm font-medium text-slate-700">
            until Kickoff
          </p>

          <p className="text-center text-sm text-slate-600">
            Come back at {kickoffTime} on {kickoffDate} to watch live!
          </p>
        </>
      )}

      <div className="mt-4 flex justify-center">
        <a
          href="/watch/kickoff"
          className={`inline-flex items-center gap-2 rounded-lg px-6 py-3
            text-lg font-semibold transition-colors hover:no-underline ${
              isWithin24Hours
                ? 'bg-green-500 text-white hover:bg-green-600'
                : `pointer-events-none cursor-not-allowed bg-slate-300
                  text-slate-400`
            }`}
          aria-disabled={!isWithin24Hours}
          tabIndex={isWithin24Hours ? undefined : -1}
        >
          <BiPlayFill className="h-5 w-5" />
          Watch Kickoff Live
        </a>
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-center">
        <a
          href="https://www.firstinspires.org/robotics/frc/game-and-season"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 rounded-lg
            bg-blue-100 px-4 py-2 text-sm font-medium text-primary
            transition-colors hover:bg-blue-200 hover:no-underline"
        >
          <BiInfoCircleFill className="h-4 w-4" />
          <span>{year} FRC Game Resources</span>
        </a>
      </div>
    </div>
  );
}

function CountdownUnit({
  value,
  label,
  fullLabel,
}: {
  value: number | string;
  label: string;
  fullLabel: string;
}) {
  return (
    <div className="flex flex-col items-center">
      <div
        className="flex h-16 w-16 items-center justify-center rounded-lg
          bg-slate-300 sm:h-20 sm:w-20"
      >
        <span
          className="font-mono text-3xl font-bold text-slate-800 sm:text-4xl"
        >
          {value}
        </span>
      </div>
      <span className="mt-1 text-xs font-medium text-slate-600 sm:hidden">
        {label}
      </span>
      <span className="mt-1 hidden text-xs font-medium text-slate-600 sm:block">
        {fullLabel}
      </span>
    </div>
  );
}
