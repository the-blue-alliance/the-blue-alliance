import { Link, createFileRoute } from '@tanstack/react-router';

import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/privacy')({
  headers: publicCacheControlHeaders(),
  component: Privacy,
});

function Privacy(): React.JSX.Element {
  return (
    <div className="container max-w-4xl py-8">
      <div className="typeset">
        <h1>Privacy Policy</h1>
        <p>
          Updated: <span className="font-bold">May 19, 2017</span>
        </p>
        <h2>The short version</h2>
        <p>
          We collect your information only with your consent; we only collect
          the minimum amount of personal information that is necessary to
          fulfill the purpose of your interaction with us; we don&apos;t sell it
          to third parties; and we only use it as this Privacy Policy describes.
          Of course, the short version doesn&apos;t tell you everything, so
          please read on for more details!
        </p>

        <h2>What information The Blue Alliance collects and why</h2>
        <h3>Information from website browsers</h3>
        <p>
          If you&apos;re <b>just browsing the website</b>, we collect the same
          basic information that most websites collect. We use common internet
          technologies, such as cookies and web server logs. This is stuff we
          collect from everybody, whether they have an account or not.
        </p>
        <p>
          The information we collect about all visitors to our website includes
          the visitor&apos;s browser type, language preference, referring site,
          additional websites requested, and the date and time of each visitor
          request. We also collect potentially personally-identifying
          information like Internet Protocol (IP) addresses.
        </p>
        <h4>Why do we collect this?</h4>
        <p>
          We collect this information to better understand how our website
          visitors use The Blue Alliance, and to monitor and protect the
          security of the website.
        </p>
        <h3>Information from users with accounts</h3>
        <p>
          We use Google sign-in for our accounts. If you{' '}
          <b>create an account</b> with us, only your email address is shared
          with us, not your password or any other personal information. You also
          have the option to give us more information, such as your name, which
          may include &quot;User Personal Information.&quot;
        </p>
        <h4>Why do we collect this?</h4>
        <ul>
          <li>
            We use your name to personalize your experience with The Blue
            Alliance.
          </li>
          <li>
            We use your email address as a way to identify you across devices so
            that you can have a consistent experience across The Blue Alliance.
          </li>
          <li>
            We use your email to communicate with you with information regarding
            approved suggestions and API key requests.
          </li>
        </ul>

        <h2>What information The Blue Alliance does not collect</h2>
        <p>
          We do not intentionally collect sensitive personal information, such
          as social security numbers, genetic data, health information, or
          religious information. If you&apos;re a child under the age of 13, you
          may not have an account on The Blue Alliance. The Blue Alliance does
          not knowingly collect information from or direct any of our content
          specifically to children under 13. If we learn or have reason to
          suspect that you are a user who is under the age of 13, we will have
          to close your account.
        </p>

        <h2>How we share the information we collect</h2>
        <p>
          We <b>do not</b> share, sell, rent, or trade any User Personal
          Information with third parties.
        </p>

        <h2>Our use of cookies and tracking</h2>
        <h3>Cookies</h3>
        <p>
          The Blue Alliance uses cookies to make interactions with our service
          easy and meaningful. We use cookies (and similar technologies, like
          HTML5 localStorage) to keep you logged in and remember your
          preferences.
        </p>
        <p>
          A cookie is a small piece of text that our web server stores on your
          computer or mobile device, which your browser sends to us when you
          return to our site. Cookies do not necessarily identify you if you are
          merely visiting The Blue Alliance; however, a cookie may store a
          unique identifier for each logged in user. The cookies The Blue
          Alliance sets are essential for the operation of the website, or are
          used for performance or functionality. By using our website, you agree
          that we can place these types of cookies on your computer or device.
          If you disable your browser or device&apos;s ability to accept
          cookies, you will not be able to log in or use The Blue
          Alliance&apos;s services.
        </p>
        <h3>Google Analytics</h3>
        <p>
          We use Google Analytics as a third party tracking service, but we
          don&apos;t use it to track you individually or collect your User
          Personal Information. We use Google Analytics to collect information
          about how our website performs and how our users, in general, navigate
          through and use The Blue Alliance. This helps us evaluate our
          users&apos; use of The Blue Alliance; compile statistical reports on
          activity; and improve our content and website performance.
        </p>
        <p>
          Google Analytics gathers certain simple, non-personally identifying
          information over time, such as your IP address, browser type, internet
          service provider, referring and exit pages, time stamp, and similar
          data about your use of The Blue Alliance. We do not link this
          information to any of your personal information such as your user
          name.
        </p>
        <p>
          The Blue Alliance will not, nor will we allow any third party to, use
          the Google Analytics tool to track our users individually; collect any
          User Personal Information other than IP address; or correlate your IP
          address with your identity. Google provides further information about
          its own privacy practices and offers a browser add-on to opt out of
          Google Analytics tracking.
        </p>
        <p>
          Certain pages on our site may set other third party cookies. For
          example, we may embed content, such as videos, from another site that
          sets a cookie. While we try to minimize these third party cookies, we
          can&apos;t always control what cookies this third party content sets.
        </p>

        <h2>License</h2>
        <p>
          This Privacy Policy is adapted from{' '}
          <a href="https://help.github.com/articles/github-privacy-statement/">
            GitHub&apos;s Privacy Statement
          </a>{' '}
          and is licensed under the{' '}
          <a href="https://creativecommons.org/licenses/by/4.0/">
            Creative Commons Attribution license
          </a>
          . You may use it freely under the terms of the Creative Commons
          license.
        </p>

        <h2>Contact</h2>
        <p>
          <Link to="/contact">Contact us</Link> if you have questions regarding
          our Privacy Policy.
        </p>
      </div>
    </div>
  );
}
