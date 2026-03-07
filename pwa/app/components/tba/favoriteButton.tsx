import { useEffect, useState } from 'react';

import BiStar from '~icons/bi/star';
import BiStarFill from '~icons/bi/star-fill';

import type { ModelType } from '~/api/tba/mobile/types.gen';
import { useAuth } from '~/components/tba/auth/auth';
import SignInWithAppleButton from '~/components/tba/auth/signInWithAppleButton';
import SignInWithGoogleButton from '~/components/tba/auth/signInWithGoogleButton';
import { Button } from '~/components/ui/button';
import {
  Credenza,
  CredenzaBody,
  CredenzaContent,
  CredenzaDescription,
  CredenzaHeader,
  CredenzaTitle,
} from '~/components/ui/credenza';
import { useMyTBA } from '~/lib/hooks/useMyTBA';

interface FavoriteButtonProps {
  modelKey: string;
  modelType: ModelType;
}

export default function FavoriteButton({
  modelKey,
  modelType,
}: FavoriteButtonProps) {
  const { user } = useAuth();
  const { isFavorite, toggleFavorite, isPending } = useMyTBA(
    modelKey,
    modelType,
  );
  const [loginOpen, setLoginOpen] = useState(false);

  useEffect(() => {
    if (user && loginOpen) {
      setLoginOpen(false);
    }
  }, [user, loginOpen]);

  const handleClick = () => {
    if (!user) {
      setLoginOpen(true);
      return;
    }
    toggleFavorite();
  };

  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        onClick={handleClick}
        disabled={isPending}
        aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
      >
        {isFavorite ? (
          <BiStarFill className="h-5 w-5 text-yellow-500" />
        ) : (
          <BiStar className="h-5 w-5" />
        )}
      </Button>
      <Credenza open={loginOpen} onOpenChange={setLoginOpen}>
        <CredenzaContent className="max-h-[85vh] overflow-y-auto">
          <CredenzaHeader>
            <CredenzaTitle>Sign in to use myTBA</CredenzaTitle>
            <CredenzaDescription>
              Sign in to favorite teams, events, and matches and manage push
              notification subscriptions.
            </CredenzaDescription>
          </CredenzaHeader>
          <CredenzaBody>
            <div className="flex flex-col gap-2 py-2">
              <SignInWithGoogleButton />
              <SignInWithAppleButton />
            </div>
          </CredenzaBody>
        </CredenzaContent>
      </Credenza>
    </>
  );
}
