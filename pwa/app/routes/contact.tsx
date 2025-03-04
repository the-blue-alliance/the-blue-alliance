import { Link } from '@remix-run/react';

import { Button } from '~/components/ui/button';

export default function Contact(): React.JSX.Element {
  return (
    <>
      <div className="flex flex-col divide-y **:mt-4">
        <div>
          <h1 className="text-3xl font-medium">Contact us</h1>
          <p>
            We&apos;d love to hear from you. Here&apos;s how to get in touch
            about different issues or questions.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Is your team&apos;s information wrong?</h3>
          <h4 className="text-xl">Team information</h4>
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
          <h4 className="text-xl">Photos, Social Media, and Robot Names</h4>
          <p>
            Some team data - like photos, CAD models, social media, and robot
            names - are provided to The Blue Alliance through crowdsourcing or
            by teams directly. Teams can use the Team Moderator codes in the
            FIRST Digital Kit of Parts to change robot names and approve or
            change media on your own team page. You can get the code for your
            team from the FIRST Digital Kit of Parts, and redeem it at the{' '}
            <Link to="/mod">TBA Team Mod dashboard</Link> Only one TBA account
            may be the &quot;team mod&quot; each year, so please choose
            carefully.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">
            Have match videos or data to add to The Blue Alliance?
          </h3>
          <p>
            Learn how you can help add match video, offseason results, report
            bad data, and more <Link to="/add-data">here.</Link>
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Want to help keep our data up to date?</h3>
          <p>
            Join{' '}
            <a href="https://www.facebook.com/groups/moardata/">
              our facebook group
            </a>{' '}
            to help add offseason results, report bad data, give us feedback,
            and more!
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Need API access?</h3>
          <p>
            You can review the{' '}
            <Link to="/apidocs">documentation for our APIs</Link> on our
            website.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Want to help improve The Blue Alliance?</h3>
          <p>
            Check out our{' '}
            <a href="https://github.com/the-blue-alliance/the-blue-alliance">
              GitHub repository
            </a>{' '}
            if you&apos;d like to help improve The Blue Alliance website or
            APIs.
          </p>
        </div>

        <div>
          <h3 className="text-2xl">Everything else...</h3>
          <p>Feel free to reach out to us!</p>
          <Button asChild>
            <a href="mailto:contact@thebluealliance.com">Email Us!</a>
          </Button>
          <Button asChild>
            <a href="https://groups.google.com/forum/#!forum/thebluealliance-developers">
              Join our Developer Mailing List!
            </a>
          </Button>
          <Button asChild>
            <a href="https://www.chiefdelphi.com/">Ask Chief Delphi Fourms!</a>
          </Button>
        </div>
      </div>
    </>
  );
}
