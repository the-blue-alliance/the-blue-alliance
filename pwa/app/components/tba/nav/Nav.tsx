import {
    NavigationMenu,
    NavigationMenuContent,
    NavigationMenuIndicator,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    NavigationMenuTrigger,
    NavigationMenuViewport,
    navigationMenuTriggerStyle,
} from "~/components/ui/navigation-menu";


import { cn } from '~/lib/utils';
import { Input } from "~/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "~/components/ui/popover";
import BiStarFill from '~icons/bi/star-fill';
import IonCalendar from '~icons/ion/calendar';
import BiPeopleFill from '~icons/bi/people-fill';
import BiCameraVideoFill from '~icons/bi/camera-video-fill';
import BiBarChartLineFill from '~icons/bi/bar-chart-line-fill';
import BiThreeDotsVertical from '~icons/bi/three-dots-vertical';
import BiPencilFill from '~icons/bi/pencil-fill';
import BiGearFill from '~icons/bi/gear-fill';

type MenuItemProps = {
    icon: React.ReactNode;
    title: string;
};

export const MenuItem = ({ icon, title }: MenuItemProps) => {
    return (
        <NavigationMenuItem>
            <NavigationMenuLink className={navigationMenuTriggerStyle() + " h-10 px-4 cursor-pointer"}>
                {icon}
                <div className="pl-2">{title}</div>
            </NavigationMenuLink>
        </NavigationMenuItem>
    )
}

export const DropMenuItem = ({ icon, title }: MenuItemProps) => {
    return (

        <NavigationMenuItem
            className={cn(
                "relative flex cursor-default select-none bg-primary items-center rounded-sm text-md outline-none transition-colors focus:bg-background focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
            )}
        >
            <NavigationMenuLink className={navigationMenuTriggerStyle() + " cursor-pointer w-full grow h-10"}>
                <div className="content-between flex flex-row grow justify-start items-center flex-wrap px-2">
                    {icon}
                    <div className="pl-2 antialiased">{title}</div>
                </div>

            </NavigationMenuLink>
        </NavigationMenuItem>
    )
}

export const Nav = () => {
    return (
        <div className="flex fixed p-2 w-full flex-grow grow justify-center bg-primary shadow-md">

            <NavigationMenu>
                <NavigationMenuList className="flex flex-grow w-full">
                    <img src="https://www.thebluealliance.com/images/tba_lamp.svg" className="h-8 pr-4 w-8" />
                    <div className="text-2xl text-white whitespace-nowrap pr-2">The Blue Alliance</div>
                    <div className="grow" />
                    <MenuItem icon={<BiStarFill />} title="myTBA" />
                    <MenuItem icon={<IonCalendar />} title="Events" />
                    <MenuItem icon={<BiPeopleFill />} title="Teams" />
                    <MenuItem icon={<BiCameraVideoFill />} title="GameDay" />
                    <MenuItem icon={<BiBarChartLineFill />} title="Insights" />
                    <Popover>
                        <PopoverTrigger><MenuItem title="More" icon={<BiThreeDotsVertical />} /> </PopoverTrigger>
                        <PopoverContent sideOffset={12} alignOffset={-2} align="start" className={cn("mt-6 bg-primary px-1 py-1 w-30 m-0 border-none drop-shadow-lg shadow-l rounded-md ")}>
                            <DropMenuItem icon={<BiPencilFill />} title="Blog" />
                            <DropMenuItem icon={<BiGearFill />} title="Account" />
                        </PopoverContent>
                    </Popover>

                </NavigationMenuList>
                <Input placeholder="Search" type="search" className="ml-8 h-8 bg-accent border-none focus:bg-white focus-visible:border-none focus:outline-none focus:ring-none transition-all focus:text-black" />
            </NavigationMenu>
        </div >

    )
}