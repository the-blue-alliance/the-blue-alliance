import { Link, createFileRoute } from '@tanstack/react-router';

import { Button } from '~/components/ui/button';
import { publicCacheControlHeaders } from '~/lib/utils';

export const Route = createFileRoute('/contact')({
  headers: publicCacheControlHeaders(),
  component: Contact,
});

function Contact(): React.JSX.Element {
  return (
    <div className="container max-w-4xl py-8">
      <div className="typeset">
        <h1>Contact us</h1>
        <p>
          We&apos;d love to hear from you. Here&apos;s how to get in touch about
          different issues or questions.
        </p>

        <h2>Is your team&apos;s information wrong?</h2>
        <h3>Team information</h3>
        <p>
          Most team data - like names, websites, sponsors, etc - are updated
          directly from FIRST. If your team&apos;s information is incorrect on
          The Blue Alliance, please check that it is correct on FIRST&apos;s
          website. We update our records from{' '}
          <a href="https://my.firstinspires.org/Dashboard/">
            <em>FIRST</em>&apos;s Team Information Management System
          </a>{' '}
          daily, and are unable to change your team information to anything
          other than what is listed there. You can ask your team&apos;s Lead
          Mentor to update the information in FIRST TIMS and it will update on
          The Blue Alliance within a day or two.
        </p>
        <h3>Photos, Social Media, and Robot Names</h3>
        <p>
          Some team data - like photos, CAD models, social media, and robot
          names - are provided to The Blue Alliance through crowdsourcing or by
          teams directly. Teams can use the Team Moderator codes in the FIRST
          Digital Kit of Parts to change robot names and approve or change media
          on your own team page. You can get the code for your team from the
          FIRST Digital Kit of Parts, and redeem it at the{' '}
          <a href="/mod">TBA Team Mod dashboard</a> Only one TBA account may be
          the &quot;team mod&quot; each year, so please choose carefully.
        </p>

        <h2>Have match videos or data to add to The Blue Alliance?</h2>
        <p>
          Learn how you can help add match video, offseason results, report bad
          data, and more <Link to="/add-data">here.</Link>
        </p>

        <h2>Want to help keep our data up to date?</h2>
        <p>
          Join{' '}
          <a href="https://www.facebook.com/groups/moardata/">
            our facebook group
          </a>{' '}
          to help add offseason results, report bad data, give us feedback, and
          more!
        </p>

        <h2>Need API access?</h2>
        <p>
          You can review the{' '}
          <Link to="/apidocs">documentation for our APIs</Link> on our website.
        </p>

        <h2>Want to help improve The Blue Alliance?</h2>
        <p>
          Check out our{' '}
          <a href="https://github.com/the-blue-alliance/the-blue-alliance">
            GitHub repository
          </a>{' '}
          if you&apos;d like to help improve The Blue Alliance website or APIs.
        </p>

        <h2>Everything else...</h2>
        <p>Feel free to reach out to us!</p>
        <div className="not-typeset flex flex-wrap gap-2">
          <Button
            render={<a href="mailto:contact@thebluealliance.com">Email Us!</a>}
          />
          <Button
            render={
              <a href="https://groups.google.com/forum/#!forum/thebluealliance-developers">
                Join our Developer Mailing List!
              </a>
            }
          />
          <Button
            render={
              <a href="https://www.chiefdelphi.com/">
                Ask Chief Delphi Fourms!
              </a>
            }
          />
        </div>
      </div>
    </div>
  );
}
