import { Link } from '@tanstack/react-router';
import { type JSX, useState } from 'react';

import CircleUserIcon from '~icons/lucide/circle-user-round';

import { useAuth } from '~/components/tba/auth/auth';
import { LogoutConfirmDialog } from '~/components/tba/auth/logoutConfirmDialog';
import { Avatar, AvatarFallback, AvatarImage } from '~/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '~/components/ui/dropdown-menu';
import {
  type DataSource,
  getDataSource,
  setDataSource,
} from '~/lib/dataSource';
import { getDisplayName, getInitials } from '~/lib/profileUtils';
import { useTheme } from '~/lib/theme';

export function ProfileMenu(): JSX.Element {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [logoutConfirmOpen, setLogoutConfirmOpen] = useState(false);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="Account menu"
          data-testid="profile-menu-trigger"
          className="flex cursor-pointer items-center rounded-full hover:ring-2
            hover:ring-white/40"
        >
          <Avatar className="size-8 rounded-full">
            {user?.photoURL && (
              // Google avatar URLs 403 when sent a referer
              <AvatarImage
                src={user.photoURL}
                alt=""
                referrerPolicy="no-referrer"
              />
            )}
            <AvatarFallback
              className="bg-white/20 text-xs font-medium text-white"
            >
              {user ? (
                getInitials(user.displayName, user.email)
              ) : (
                <CircleUserIcon className="size-5" />
              )}
            </AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-60">
          {user ? (
            <>
              <div className="px-2 py-1.5 text-sm">
                <div className="truncate font-medium">
                  {getDisplayName(user)}
                </div>
                <div className="truncate text-xs text-muted-foreground">
                  {user.email}
                </div>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                render={
                  <Link
                    to="/account"
                    className="text-popover-foreground hover:no-underline"
                  />
                }
              >
                Account
              </DropdownMenuItem>
            </>
          ) : (
            <DropdownMenuItem
              render={
                <Link
                  to="/account"
                  className="text-popover-foreground hover:no-underline"
                />
              }
            >
              Sign in
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuRadioGroup
            value={theme}
            onValueChange={(value) =>
              setTheme(value as 'light' | 'dark' | 'system')
            }
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Theme
            </DropdownMenuLabel>
            <DropdownMenuRadioItem value="light">Light</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="dark">Dark</DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="system">System</DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
          {import.meta.env.DEV && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuRadioGroup
                value={getDataSource()}
                onValueChange={(value) => {
                  // The API client is configured at startup, so a reload is
                  // the reliable way to swap data sources
                  setDataSource(value as DataSource);
                  window.location.reload();
                }}
              >
                <DropdownMenuLabel className="text-xs text-muted-foreground">
                  Data source (dev only)
                </DropdownMenuLabel>
                <DropdownMenuRadioItem value="prod">
                  Production
                </DropdownMenuRadioItem>
                <DropdownMenuRadioItem value="local">
                  Local dev
                </DropdownMenuRadioItem>
              </DropdownMenuRadioGroup>
            </>
          )}
          {user && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setLogoutConfirmOpen(true)}>
                Logout
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <LogoutConfirmDialog
        open={logoutConfirmOpen}
        onOpenChange={setLogoutConfirmOpen}
        onConfirm={() => void logout()}
      />
    </>
  );
}
