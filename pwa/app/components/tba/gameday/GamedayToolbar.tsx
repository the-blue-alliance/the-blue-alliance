import { useState } from 'react';

import CheckIcon from '~icons/lucide/check';
import LayoutGridIcon from '~icons/lucide/layout-grid';
import MessageSquareIcon from '~icons/lucide/message-square';
import RotateCcwIcon from '~icons/lucide/rotate-ccw';

import { LayoutIcon } from '~/components/tba/gameday/LayoutIcon';
import { Button } from '~/components/ui/button';
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from '~/components/ui/drawer';
import { Separator } from '~/components/ui/separator';
import TbaLamp from '~/images/tba/tba-lamp.svg';
import { useGameday } from '~/lib/gameday/context';
import { LAYOUT_DISPLAY_ORDER, getLayoutById } from '~/lib/gameday/layouts';

export function GamedayToolbar() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { state, setLayout, toggleChatSidebar, resetWebcasts } = useGameday();

  return (
    <>
      <header
        className="flex h-10 shrink-0 items-center gap-2 border-b
          border-slate-700 bg-primary px-4"
      >
        {/* TBA branding */}
        <a
          href="/"
          className="flex items-center gap-2 text-white no-underline
            hover:no-underline"
        >
          <img src={TbaLamp} alt="TBA" className="size-6" />
          <span className="text-lg font-medium">
            GameDay{' '}
            <span className="ml-1 text-sm text-white/70">
              by The Blue Alliance
            </span>
          </span>
        </a>

        <div className="flex-1" />

        {/* Configure layout button */}
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-2 text-white hover:bg-white/10 hover:text-white"
          onClick={() => setDrawerOpen(true)}
        >
          {state.layoutId !== null && (
            <LayoutIcon
              layoutId={state.layoutId}
              className="h-4 w-7"
              color="white"
            />
          )}
          <span className="hidden sm:inline">Configure Layout</span>
          <LayoutGridIcon className="h-4 w-4 sm:hidden" />
        </Button>
      </header>

      {/* Settings drawer */}
      <Drawer open={drawerOpen} onOpenChange={setDrawerOpen} direction="right">
        <DrawerContent
          className="fixed inset-y-0 right-0 left-auto mt-0 h-full w-80
            rounded-t-none rounded-l-[10px] sm:w-96"
          showHandle={false}
        >
          <DrawerHeader>
            <DrawerTitle>Configure GameDay</DrawerTitle>
            <DrawerDescription>
              Choose a layout and customize your viewing experience
            </DrawerDescription>
          </DrawerHeader>

          <div className="overflow-y-auto px-4">
            {/* Layout selection */}
            <h3 className="mb-2 text-sm font-semibold text-primary">
              Video Grid Layout
            </h3>
            <div className="grid grid-cols-1 gap-2">
              {LAYOUT_DISPLAY_ORDER.map((layoutId) => {
                const layout = getLayoutById(layoutId);
                if (!layout) return null;

                const isSelected = state.layoutId === layoutId;

                return (
                  <button
                    key={layoutId}
                    onClick={() => {
                      setLayout(layoutId);
                      setDrawerOpen(false);
                    }}
                    className={`flex cursor-pointer items-center gap-2
                    rounded-md border p-2 transition-colors ${
                      isSelected
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:bg-accent'
                    }`}
                  >
                    <LayoutIcon
                      layoutId={layoutId}
                      className="h-5 w-8 shrink-0"
                    />
                    <span className="truncate text-sm">{layout.name}</span>
                    {isSelected && (
                      <CheckIcon
                        className="ml-auto h-4 w-4 shrink-0 text-primary"
                      />
                    )}
                  </button>
                );
              })}
            </div>

            <Separator className="my-4" />

            {/* Sidebar toggles */}
            <h3 className="mb-2 text-sm font-semibold text-primary">
              Sidebars
            </h3>
            <div className="space-y-2">
              <button
                onClick={toggleChatSidebar}
                className="flex w-full cursor-pointer items-center
                  justify-between rounded-md border border-border p-3
                  transition-colors hover:bg-accent"
              >
                <div className="flex items-center gap-2">
                  <MessageSquareIcon className="h-4 w-4" />
                  <span>Twitch Chat</span>
                </div>
                <span
                  className={`text-sm
                    ${state.chatSidebarVisible ? 'text-green-600' : 'text-muted-foreground'}`}
                >
                  {state.chatSidebarVisible ? 'Visible' : 'Hidden'}
                </span>
              </button>
            </div>

            <Separator className="my-4" />

            {/* Reset */}
            <Button
              variant="destructive"
              className="w-full gap-2"
              onClick={() => {
                resetWebcasts();
                setDrawerOpen(false);
              }}
            >
              <RotateCcwIcon className="h-4 w-4" />
              Reset All Webcasts
            </Button>
          </div>

          <DrawerFooter>
            <DrawerClose asChild>
              <Button variant="outline">Close</Button>
            </DrawerClose>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    </>
  );
}
