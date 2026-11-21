import { cn } from 'cn';
import { FirebaseError } from 'firebase/app';
import {
  AuthProvider,
  signInWithPopup,
  signInWithRedirect,
} from 'firebase/auth';

import { auth } from '~/firebase/firebaseConfig';
import { createLogger } from '~/lib/utils';

const authLogger = createLogger('auth');

const REDIRECT_FALLBACK_CODES = new Set([
  'auth/popup-blocked',
  'auth/cancelled-popup-request',
  'auth/operation-not-supported-in-this-environment',
]);

export default function SignInButton({
  provider,
  logo,
  text,
  className,
}: {
  provider: AuthProvider;
  logo: string;
  text: string;
  className: string;
}) {
  const handleSignIn = () => {
    if (!auth) return;
    const activeAuth = auth;
    signInWithPopup(activeAuth, provider).catch((error: unknown) => {
      if (
        error instanceof FirebaseError &&
        REDIRECT_FALLBACK_CODES.has(error.code)
      ) {
        signInWithRedirect(activeAuth, provider).catch(
          (redirectError: unknown) => {
            authLogger.error(
              { error: redirectError },
              'Error during redirect sign-in',
            );
          },
        );
        return;
      }
      authLogger.error({ error }, 'Error during sign-in');
    });
  };

  return (
    <button
      className={cn(
        `flex h-10 w-full cursor-pointer items-center justify-center rounded
        text-base`,
        className,
      )}
      onClick={handleSignIn}
    >
      <div className="flex h-9 w-9 items-center justify-center">
        <img src={logo} alt={`${text} logo`} className="h-5 w-5" />
      </div>
      <span className="mx-auto">{text}</span>
    </button>
  );
}
