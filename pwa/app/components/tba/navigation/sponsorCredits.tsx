import { useQuery } from '@tanstack/react-query';
import { cn } from 'cn';
import { Fragment } from 'react';

import type { Sponsor } from '~/api/tba/read';
import { getSponsorsOptions } from '~/api/tba/read/@tanstack/react-query.gen';
import { STALE_TIME } from '~/lib/queryClient';

/**
 * The platinum sponsors from `/api/v3/sponsors`. Empty while loading or if the
 * request fails, so callers simply render nothing.
 */
export function usePlatinumSponsors(): Sponsor[] {
  const { data } = useQuery({
    ...getSponsorsOptions({}),
    staleTime: STALE_TIME.SPONSORS,
  });
  return data?.sponsors ?? [];
}

function sponsorLabel(count: number): string {
  return count === 1
    ? 'Thanks to our platinum sponsor'
    : 'Thanks to our platinum sponsors';
}

function SponsorLogo({
  sponsor,
  logoUrl,
  darkLogoUrl,
  className,
}: {
  sponsor: Sponsor;
  logoUrl: string | null;
  /**
   * Shown instead of `logoUrl` in dark mode, when given. Never used alone: it
   * is a white logo, unreadable on a light background.
   */
  darkLogoUrl?: string | null;
  className?: string;
}) {
  if (!logoUrl) {
    return <span>{sponsor.name}</span>;
  }
  const isMark = sponsor.logo_style === 'mark';
  const alt = isMark ? '' : sponsor.name;
  const imgClass = cn(isMark && 'aspect-square', className);
  // brightness-90 scales the white logo to the dark-mode text color (#e5e5e5).
  const images =
    darkLogoUrl && darkLogoUrl !== logoUrl ? (
      <>
        <img
          src={logoUrl}
          alt={alt}
          loading="lazy"
          className={cn(imgClass, 'dark:hidden')}
        />
        <img
          src={darkLogoUrl}
          alt={alt}
          loading="lazy"
          className={cn(imgClass, 'hidden brightness-90 dark:inline')}
        />
      </>
    ) : (
      <img src={logoUrl} alt={alt} loading="lazy" className={imgClass} />
    );
  if (isMark) {
    return (
      <span className="inline-flex items-center gap-1.5">
        {images}
        {sponsor.name}
      </span>
    );
  }
  return images;
}

/** Sponsor credit for the desktop footer, on the page background. */
export function FooterSponsorCredit() {
  const sponsors = usePlatinumSponsors();
  if (sponsors.length === 0) {
    return null;
  }

  return (
    <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
      <span>{sponsorLabel(sponsors.length)}</span>
      {sponsors.map((sponsor) => (
        // The space keeps names apart in the text read aloud and copied
        <Fragment key={sponsor.name}>
          {' '}
          <a href={sponsor.url} target="_blank" rel="noreferrer noopener">
            <SponsorLogo
              sponsor={sponsor}
              logoUrl={sponsor.logo_url}
              darkLogoUrl={sponsor.logo_url_dark}
              className="inline h-4 w-auto"
            />
          </a>
        </Fragment>
      ))}
    </span>
  );
}

/** Sponsor credit for the bottom of the brand-blue mobile menu. */
export function MobileMenuSponsorCredit({
  animationDelayMs,
}: {
  animationDelayMs: number;
}) {
  const sponsors = usePlatinumSponsors();
  if (sponsors.length === 0) {
    return null;
  }

  return (
    <div
      className="animate-navigation-item-fade-in border-t border-white/10 py-4
        text-xs text-white opacity-0 motion-safe:[--nav-item-shift:-8px]"
      style={{ animationDelay: `${animationDelayMs}ms` }}
    >
      <p className="text-white/60">{sponsorLabel(sponsors.length)}</p>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
        {sponsors.map((sponsor) => (
          <a
            key={sponsor.name}
            href={sponsor.url}
            target="_blank"
            rel="noreferrer noopener"
            className="text-sm font-medium text-white hover:no-underline"
          >
            <SponsorLogo
              sponsor={sponsor}
              logoUrl={sponsor.logo_url_dark}
              className="h-5 w-auto"
            />
          </a>
        ))}
      </div>
    </div>
  );
}
