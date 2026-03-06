import { P, match } from 'ts-pattern';

import LogosTwitch from '~icons/logos/twitch';
import LogosYoutubeIcon from '~icons/logos/youtube-icon';
import MdiVideoOutline from '~icons/mdi/video-outline';
import SimpleIconsFacebook from '~icons/simple-icons/facebook';
import SimpleIconsGithub from '~icons/simple-icons/github';
import SimpleIconsGitlab from '~icons/simple-icons/gitlab';
import SimpleIconsInstagram from '~icons/simple-icons/instagram';
import SimpleIconsX from '~icons/simple-icons/x';

import { Media, Webcast } from '~/api/tba/read';
import InlineIcon from '~/components/tba/inlineIcon';
import { Badge } from '~/components/ui/badge';

interface MediaBadgeProps {
  className?: string;
  icon: React.ReactNode;
  href: string;
  label: string;
}

function MediaBadge({ className, icon, href, label }: MediaBadgeProps) {
  return (
    <Badge className={className} variant="secondary">
      <a href={href} className="text-secondary-foreground">
        <InlineIcon>
          {icon}
          {label}
        </InlineIcon>
      </a>
    </Badge>
  );
}

export function MediaIcon({
  media,
  className,
}: {
  media: Media;
  className?: string;
}) {
  const props = match(media.type)
    .with(P.union('youtube', 'youtube-channel'), () => ({
      icon: <LogosYoutubeIcon />,
      href: `https://www.youtube.com/${media.foreign_key}`,
    }))
    .with('facebook-profile', () => ({
      icon: <SimpleIconsFacebook />,
      href: `https://www.facebook.com/${media.foreign_key}`,
    }))
    .with('github-profile', () => ({
      icon: <SimpleIconsGithub />,
      href: `https://github.com/${media.foreign_key}`,
    }))
    .with('instagram-profile', () => ({
      icon: <SimpleIconsInstagram />,
      href: `https://www.instagram.com/${media.foreign_key}`,
    }))
    .with('twitter-profile', () => ({
      icon: <SimpleIconsX />,
      href: `https://x.com/${media.foreign_key}`,
    }))
    .with('gitlab-profile', () => ({
      icon: <SimpleIconsGitlab />,
      href: `https://gitlab.com/${media.foreign_key}`,
    }))
    .otherwise(() => null);

  if (!props) return null;
  return (
    <MediaBadge className={className} {...props} label={media.foreign_key} />
  );
}

export function WebcastIcon({
  webcast,
  className,
}: {
  webcast: Webcast;
  className?: string;
}) {
  const props = match(webcast.type)
    .with('youtube', () => ({
      icon: <LogosYoutubeIcon />,
      href: `https://www.youtube.com/watch?v=${webcast.channel}`,
      label: webcast.channel,
    }))
    .with('twitch', () => ({
      icon: <LogosTwitch />,
      href: `https://www.twitch.tv/${webcast.channel}`,
      label: webcast.channel,
    }))
    .otherwise(() => ({
      icon: <MdiVideoOutline />,
      href: '#',
      label: webcast.type,
    }));

  return <MediaBadge className={className} {...props} />;
}
