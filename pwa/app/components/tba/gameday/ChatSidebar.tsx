import { useState } from 'react';

import ChevronUpIcon from '~icons/lucide/chevron-up';
import MessageSquareIcon from '~icons/lucide/message-square';

import { Button } from '~/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '~/components/ui/dialog';
import { useGameday } from '~/lib/gameday/context';

const SIDEBAR_WIDTH = 300;

export function ChatSidebar() {
  const { state, setCurrentChat } = useGameday();
  const [selectorOpen, setSelectorOpen] = useState(false);

  if (!state.chatSidebarVisible) return null;

  const hostname =
    typeof window !== 'undefined' ? window.location.hostname : 'localhost';

  // Get available chat channels from displayed webcasts (Twitch only)
  const availableChats = Object.values(state.webcastsById)
    .filter((w) => w.webcast.type === 'twitch')
    .map((w) => ({
      channel: w.webcast.channel,
      name: w.name,
    }));

  const currentChatInfo = availableChats.find(
    (c) => c.channel === state.currentChat,
  );
  const chatSrc = state.currentChat
    ? `https://www.twitch.tv/embed/${state.currentChat}/chat?parent=${hostname}&darkpopout`
    : '';

  return (
    <div
      className="flex h-full flex-col border-l border-neutral-700
        bg-neutral-950"
      style={{ width: SIDEBAR_WIDTH }}
    >
      {/* Chat iframe */}
      <div className="flex-1">
        {chatSrc ? (
          <iframe
            src={chatSrc}
            title="Twitch chat"
            className="h-full w-full"
            sandbox="allow-scripts allow-same-origin allow-popups"
          />
        ) : (
          <div
            className="flex h-full flex-col items-center justify-center
              text-center text-neutral-400"
          >
            <MessageSquareIcon className="mb-2 h-8 w-8" />
            <p>No chat selected</p>
            <p className="mt-1 text-sm">Select a chat below</p>
          </div>
        )}
      </div>

      {/* Chat selector bar */}
      <button
        onClick={() => setSelectorOpen(true)}
        className="flex h-9 shrink-0 cursor-pointer items-center justify-between
          border-t border-neutral-800 bg-primary px-3 text-white
          transition-colors hover:bg-primary/90"
      >
        <span className="truncate text-sm font-medium">
          {currentChatInfo?.name ?? 'Select a chat'}
        </span>
        <ChevronUpIcon className="h-4 w-4" />
      </button>

      {/* Chat selector dialog */}
      <Dialog open={selectorOpen} onOpenChange={setSelectorOpen}>
        <DialogContent
          // Auto focus on the content area and not first element
          onOpenAutoFocus={(e) => {
            e.preventDefault();
            (e.currentTarget as HTMLElement)?.focus();
          }}
          className="max-w-sm p-0"
        >
          <DialogHeader className="border-b px-4 py-3">
            <DialogTitle>Select a chat</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col py-2">
            {availableChats.length === 0 ? (
              <div className="px-4 py-4 text-center text-muted-foreground">
                No Twitch chats available
              </div>
            ) : (
              availableChats.map((chat) => (
                <Button
                  key={chat.channel}
                  variant="ghost"
                  className="justify-start rounded-none px-4 py-2"
                  onClick={() => {
                    setCurrentChat(chat.channel);
                    setSelectorOpen(false);
                  }}
                >
                  {chat.name}
                  {chat.channel === state.currentChat && (
                    <span className="ml-auto text-primary">✓</span>
                  )}
                </Button>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
