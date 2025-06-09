/* eslint-disable @typescript-eslint/no-non-null-assertion */
import {
  AuthProvider,
  browserLocalPersistence,
  setPersistence,
  signInWithPopup,
} from 'firebase/auth';
import { useNavigate } from 'react-router';

import { auth } from '~/firebase/firebaseConfig';
import { cn } from '~/lib/utils';

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
  const navigate = useNavigate();

  const handleSignIn = () => {
    setPersistence(auth!, browserLocalPersistence)
      .then(() => signInWithPopup(auth!, provider))
      .then((result) => {
        return result.user.getIdToken();
      })
      .then((idToken) => {
        return idToken;
      })
      .then((idToken) => {
        return fetch('/auth/session', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${idToken}`,
          },
        });
      })
      .then(() => {
        return navigate('/account');
      })
      .catch((error: unknown) => {
        console.error('Error during sign-in:', error);
      });
  };

  return (
    <button
      className={cn(
        'flex h-10 w-full cursor-pointer items-center justify-center rounded text-base',
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
