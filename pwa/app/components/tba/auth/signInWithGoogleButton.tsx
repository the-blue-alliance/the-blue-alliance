import { GoogleAuthProvider } from 'firebase/auth';

import SignInButton from '~/components/tba/auth/signInButton';
import GoogleLogo from '~/images/sign-in/google_sign_in_logo.svg';

export default function SignInWithGoogleButton() {
  const provider = new GoogleAuthProvider();
  return (
    <SignInButton
      provider={provider}
      logo={GoogleLogo}
      text="Sign in with Google"
      className="border bg-white text-black transition-colors duration-300
        ease-in-out hover:bg-neutral-100 active:bg-neutral-200"
    />
  );
}
