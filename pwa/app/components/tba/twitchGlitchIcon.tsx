import type { SVGProps } from 'react';

// Twitch's current "Glitch" mark in Twitch Purple, from the official brand
// kit at https://brand.twitch.com (glitch_flat_purple.svg). The white fill
// inside the bubble is part of the asset and keeps the mark legible on dark
// backgrounds, where Twitch's own guidelines show this same variant.
export default function TwitchGlitchIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 2400 2800" aria-hidden="true" {...props}>
      <path
        fill="#fff"
        d="M2200 1300l-400 400h-400l-350 350v-350H600V200h1600z"
      />
      <g fill="#9146ff">
        <path d="M500 0L0 500v1800h600v500l500-500h400l900-900V0zm1700 1300l-400 400h-400l-350 350v-350H600V200h1600z" />
        <path d="M1700 550h200v600h-200zm-550 0h200v600h-200z" />
      </g>
    </svg>
  );
}
