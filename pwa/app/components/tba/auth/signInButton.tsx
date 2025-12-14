import { AuthProvider, signInWithPopup } from 'firebase/auth';

import { auth } from '~/firebase/firebaseConfig';
import { cn, createLogger } from '~/lib/utils';

const authLogger = createLogger('auth');

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
    signInWithPopup(auth, provider).catch((error: unknown) => {
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
