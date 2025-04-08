import { Link } from 'react-router';

import BiBarChartLineFill from '~icons/bi/bar-chart-line-fill';
import BiCameraVideoFill from '~icons/bi/camera-video-fill';
import BiCartFill from '~icons/bi/cart-fill';
import BiGearFill from '~icons/bi/gear-fill';
import BiPencilFill from '~icons/bi/pencil-fill';
import BiPeopleFill from '~icons/bi/people-fill';
import BiStarFill from '~icons/bi/star-fill';
import BiThreeDotsVertical from '~icons/bi/three-dots-vertical';
import IonCalendar from '~icons/ion/calendar';
import MdiMenu from '~icons/mdi/menu';

import GlobalLoadingProgress from '~/components/tba/globalLoadingProgress';
import InlineIcon from '~/components/tba/inlineIcon';
import Searchbar from '~/components/tba/searchbar';
import { Button } from '~/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '~/components/ui/sheet';
import lamp from '~/images/tba/tba-lamp.svg';

export default function Navbar() {
  return (
    <div>
      <GlobalLoadingProgress />
      <nav className="flex h-[3rem] flex-row items-center justify-between bg-primary">
        <div className="pl-8 text-2xl">
          <Link to="/" className="text-nowrap text-white">
            <InlineIcon>
              <img
                src={lamp}
                className="size-6 max-w-none"
                alt="The Blue Alliance Logo"
              />
              The Blue Alliance
            </InlineIcon>
          </Link>
        </div>

        <div className="hidden flex-row items-center gap-x-4 pr-8 text-base lg:flex">
          <Link to="/mytba" className="text-white">
            <InlineIcon>
              <BiStarFill />
              myTBA
            </InlineIcon>
          </Link>

          <Link to="/events" className="text-white">
            <InlineIcon>
              <IonCalendar />
              Events
            </InlineIcon>
          </Link>

          <Link to="/teams" className="text-white">
            <InlineIcon>
              <BiPeopleFill />
              Teams
            </InlineIcon>
          </Link>

          <Link to="/gameday" className="text-white">
            <InlineIcon>
              <BiCameraVideoFill />
              GameDay
            </InlineIcon>
          </Link>

          <Link to="/insights" className="text-white">
            <InlineIcon>
              <BiBarChartLineFill />
              Insights
            </InlineIcon>
          </Link>

          <DropdownMenu>
            <DropdownMenuTrigger className="text-white">
              <InlineIcon>
                <BiThreeDotsVertical />
                More
              </InlineIcon>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>
                <Link to="/blog">
                  <InlineIcon>
                    <BiPencilFill />
                    Blog
                  </InlineIcon>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Link to="/swag">
                  <InlineIcon>
                    <BiCartFill />
                    Swag
                  </InlineIcon>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Link to="/account">
                  <InlineIcon>
                    <BiGearFill />
                    Account
                  </InlineIcon>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div>
            <Searchbar />
          </div>
        </div>

        <div className="visible pr-8 lg:invisible">
          <Sheet>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="cursor-pointer bg-primary hover:bg-primary"
              >
                <MdiMenu className="h-5 w-5 text-white" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent className="w-[25ch] max-w-[25ch]">
              <SheetHeader>
                <SheetTitle>
                  <Link to="/">The Blue Alliance</Link>
                </SheetTitle>
                <SheetDescription>
                  <Link to="/mytba">
                    <InlineIcon>
                      <BiStarFill />
                      myTBA
                    </InlineIcon>
                  </Link>

                  <Link to="/events">
                    <InlineIcon>
                      <IonCalendar />
                      Events
                    </InlineIcon>
                  </Link>

                  <Link to="/teams">
                    <InlineIcon>
                      <BiPeopleFill />
                      Teams
                    </InlineIcon>
                  </Link>

                  <Link to="/gameday">
                    <InlineIcon>
                      <BiCameraVideoFill />
                      GameDay
                    </InlineIcon>
                  </Link>

                  <Link to="/insights">
                    <InlineIcon>
                      <BiBarChartLineFill />
                      Insights
                    </InlineIcon>
                  </Link>

                  <Link to="/blog">
                    <InlineIcon>
                      <BiPencilFill />
                      Blog
                    </InlineIcon>
                  </Link>

                  <Link to="/swag">
                    <InlineIcon>
                      <BiCartFill />
                      Swag
                    </InlineIcon>
                  </Link>

                  <Link to="/account">
                    <InlineIcon>
                      <BiGearFill />
                      Account
                    </InlineIcon>
                  </Link>
                </SheetDescription>
              </SheetHeader>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </div>
  );
}
