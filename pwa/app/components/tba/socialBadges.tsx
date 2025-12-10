import LogosFacebook from '~icons/logos/facebook';
import LogosGithubIcon from '~icons/logos/github-icon';
import LogosGitlab from '~icons/logos/gitlab';
import LogosInstagramIcon from '~icons/logos/instagram-icon';
import LogosTwitch from '~icons/logos/twitch';
import LogosYoutubeIcon from '~icons/logos/youtube-icon';
import MdiVideoOutline from '~icons/mdi/video-outline';
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
  switch (media.type) {
    case 'youtube':
    case 'youtube-channel':
      return (
        <MediaBadge
          className={className}
          icon={<LogosYoutubeIcon />}
          href={`https://www.youtube.com/${media.foreign_key}`}
          label={media.foreign_key}
        />
      );
    case 'facebook-profile':
      return (
        <MediaBadge
          className={className}
          icon={<LogosFacebook />}
          href={`https://www.facebook.com/${media.foreign_key}`}
          label={media.foreign_key}
        />
      );
    case 'github-profile':
      return (
        <MediaBadge
          className={className}
          icon={<LogosGithubIcon />}
          href={`https://github.com/${media.foreign_key}`}
          label={media.foreign_key}
        />
      );
    case 'instagram-profile':
      return (
        <MediaBadge
          className={className}
          icon={<LogosInstagramIcon />}
          href={`https://www.instagram.com/${media.foreign_key}`}
          label={media.foreign_key}
        />
      );
    case 'twitter-profile':
      return (
        <MediaBadge
          className={className}
          icon={<SimpleIconsX />}
          href={`https://x.com/${media.foreign_key}`}
          label={media.foreign_key}
        />
      );
    case 'gitlab-profile':
      return (
        <MediaBadge
          className={className}
          icon={<LogosGitlab />}
          href={`https://gitlab.com/${media.foreign_key}`}
          label={media.foreign_key}
        />
      );
    default:
      return null;
  }
}

export function WebcastIcon({
  webcast,
  className,
}: {
  webcast: Webcast;
  className?: string;
}) {
  switch (webcast.type) {
    case 'youtube':
      return (
        <MediaBadge
          className={className}
          icon={<LogosYoutubeIcon />}
          href={`https://www.youtube.com/watch?v=${webcast.channel}`}
          label={webcast.channel}
        />
      );
    case 'twitch':
      return (
        <MediaBadge
          className={className}
          icon={<LogosTwitch />}
          href={`https://www.twitch.tv/${webcast.channel}`}
          label={webcast.channel}
        />
      );
    default:
      return (
        <MediaBadge
          className={className}
          icon={<MdiVideoOutline />}
          href={'#'}
          label={webcast.type}
        />
      );
  }
}
