import React from 'react';

import BiBellFill from '~icons/bi/bell-fill';
import BiStarFill from '~icons/bi/star-fill';

import { useAuth } from '~/components/tba/auth/context';
import SignInWithAppleButton from '~/components/tba/auth/signInWithAppleButton';
import SignInWithGoogleButton from '~/components/tba/auth/signInWithGoogleButton';
import InlineIcon from '~/components/tba/inlineIcon';

export default function Account(): React.JSX.Element {
  const { user } = useAuth();

  if (user === undefined) {
    return <LoginPage />;
  }

  return <AccountPage />;
}

function AccountPage() {
  const { user } = useAuth();

  if (user === undefined) {
    return <LoginPage />;
  }

  return (
    <div className="container max-w-4xl py-8">
      <h1 className="text-3xl">Welcome back, {user.displayName}!</h1>
    </div>
  );
}

function LoginPage() {
  return (
    <div className="container max-w-4xl py-8">
      <h1 className="text-3xl font-medium">
        Please log in to your TBA Account
      </h1>
      <section className="border-b py-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <p>
              Your account settings will be accessible on the web, our{' '}
              <a
                href="https://play.google.com/store/apps/details?id=com.thebluealliance.androidclient"
                target="_blank"
                rel="noopener noreferrer"
              >
                Android app
              </a>
              , and our{' '}
              <a
                href="https://itunes.apple.com/us/app/apple-store/id1441973916?mt=8"
                target="_blank"
                rel="noopener noreferrer"
              >
                iOS app
              </a>
              .
            </p>
          </div>
          <div className="flex flex-col gap-1">
            <SignInWithGoogleButton />
            <SignInWithAppleButton />
          </div>
        </div>
      </section>
      <section className="border-b py-6">
        <h3 className="mb-2 text-2xl font-medium">myTBA</h3>
        <div className="flex flex-col gap-1">
          <p>
            Signing in enables myTBA, which lets you customize your experience
            when using The Blue Alliance.
          </p>
          <InlineIcon>
            <BiStarFill />
            <p>
              <strong>Favorites</strong> are used for personalized content and
              quick access.
            </p>
          </InlineIcon>
          <InlineIcon>
            <BiBellFill />
            <p>
              <strong>Subscriptions</strong> are used for push notifications.
            </p>
          </InlineIcon>
        </div>
      </section>
      <section className="border-b py-6">
        <h3 className="mb-2 text-2xl font-medium">Developers</h3>
        <p>
          Build on top of The Blue Alliance! When logged in, you can generate
          API keys and manage webhooks. Our{' '}
          <a
            href="https://www.thebluealliance.com/apidocs"
            target="_blank"
            rel="noopener noreferrer"
          >
            API documentation
          </a>{' '}
          provides comprehensive guides and examples to help you integrate TBA
          data into your applications. Explore endpoints for team information,
          event details, match results, and more.
        </p>
      </section>
      <section className="border-b py-6">
        <h3 className="mb-2 text-2xl font-medium">Content Submission</h3>
        <p>
          When logged in, you can help contribute by submitting match videos,
          team photos, and more for review. Once approved, they will be
          available for everyone to see. In the future, we hope to have a
          leaderboard to show our top contributors!
        </p>
      </section>
      <section className="border-b py-6">
        <h3 className="mb-2 text-2xl font-medium">About TBA Accounts</h3>
        <p>
          The Blue Alliance uses{' '}
          <a
            href="https://myaccount.google.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            Google Accounts
          </a>{' '}
          and{' '}
          <a
            href="https://appleid.apple.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            Apple IDs
          </a>{' '}
          to handle our login. Only your email address is shared with us and it
          will always be kept private.
        </p>
      </section>
    </div>
  );
}
