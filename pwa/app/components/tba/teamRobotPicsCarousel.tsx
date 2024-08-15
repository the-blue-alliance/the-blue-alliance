import Autoplay from 'embla-carousel-autoplay';

import { Media } from '~/api/v3';
import { Card, CardContent } from '~/components/ui/card';
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from '~/components/ui/carousel';

export default function TeamRobotPicsCarousel({
  media,
}: {
  media: Media[];
}): JSX.Element {
  return (
    <Carousel
      className="mx-12 w-full max-w-xs"
      plugins={[Autoplay({ delay: 5000 })]}
    >
      <CarouselContent>
        {media.map((m, index) => (
          <CarouselItem key={index}>
            <div className="p-1">
              <Card>
                <CardContent className="flex aspect-square items-center justify-center p-6">
                  <img
                    className="size-full object-cover"
                    src={m.direct_url}
                    alt={''}
                  />
                </CardContent>
              </Card>
            </div>
          </CarouselItem>
        ))}
      </CarouselContent>
      <CarouselPrevious />
      <CarouselNext />
    </Carousel>
  );
}
