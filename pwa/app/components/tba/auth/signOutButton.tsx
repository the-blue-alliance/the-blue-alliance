import { signOut } from 'firebase/auth';
import { useNavigate } from 'react-router';

import { Button } from '~/components/ui/button';
import { auth } from '~/firebase/firebaseConfig';

export default function SignOutButton() {
  const navigate = useNavigate();

  async function handleSignOut() {
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    await signOut(auth!);
    await fetch('/auth/logout', { method: 'POST' });
    void navigate('/account');
  }

  return (
    <Button
      onClick={() => {
        void handleSignOut();
      }}
      variant={'outline'}
    >
      Sign Out
    </Button>
  );
}
