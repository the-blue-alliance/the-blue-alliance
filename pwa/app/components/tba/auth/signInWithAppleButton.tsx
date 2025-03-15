import { OAuthProvider } from 'firebase/auth';

import SignInButton from '~/components/tba/auth/signInButton';
import AppleLogo from '~/images/sign-in/apple_sign_in_logo.svg';

export default function SignInWithAppleButton() {
  const provider = new OAuthProvider('apple.com');
  return (
    <SignInButton
      provider={provider}
      logo={AppleLogo}
      text="Sign in with Apple"
      className="border-none bg-black text-white transition duration-300 ease-in-out
        hover:bg-gray-800 active:bg-gray-900"
    />
  );
}
