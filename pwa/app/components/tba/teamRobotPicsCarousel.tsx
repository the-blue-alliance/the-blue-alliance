import Autoplay from 'embla-carousel-autoplay';

import { Media } from '~/api/tba/read';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '~/components/ui/carousel';
import { getMediaImageUrl, getMediaLinkUrl } from '~/lib/mediaUtils';

export default function TeamRobotPicsCarousel({
  media,
}: {
  media: Media[];
}): React.JSX.Element {
  return (
    <Carousel className="w-full max-w-xs" plugins={[Autoplay({ delay: 5000 })]}>
      <CarouselContent className="items-center">
        {media.map((m, index) => {
          const imageUrl = getMediaImageUrl(m);
          const linkUrl = getMediaLinkUrl(m);
          if (!imageUrl) return null;

          const img = (
            <img
              className="max-h-[250px] w-full rounded object-contain"
              src={imageUrl}
              alt=""
            />
          );

          return (
            <CarouselItem key={index}>
              <div className="rounded-lg border-2 border-neutral-300">
                {linkUrl ? (
                  <a href={linkUrl} target="_blank" rel="noreferrer">
                    {img}
                  </a>
                ) : (
                  img
                )}
              </div>
            </CarouselItem>
          );
        })}
      </CarouselContent>
      {media.length > 1 && (
        <div className="mt-1 flex justify-center gap-2">
          <CarouselPrevious className="relative left-0 transform-none" />
          <CarouselNext className="relative right-0 transform-none" />
        </div>
      )}
    </Carousel>
  );
}
