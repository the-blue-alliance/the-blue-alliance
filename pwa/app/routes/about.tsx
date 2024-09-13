import { Link } from '@remix-run/react';

import { Button } from '~/components/ui/button';
import first_logo from '~/images/first_logo.png';

export default function About(): React.JSX.Element {
  return (
    <div className="container max-w-4xl">
      <h1 className="mt-8 text-3xl font-medium">About Us</h1>
      <div className="[&_p]:mb-2">
        <section className="py-6 border-b">
          <p>
            Founded in the fall of 2006, The Blue Alliance began as a website
            dedicated to providing everyone involved in the <em>FIRST</em>{' '}
            Robotics Competition (FRC) with scouting data and match videos.
            Since then, the project has grown to include developers from within
            the <em>FIRST</em>
            community from various teams all over the world. We continually
            strive to make The Blue Alliance an even more valuable resource for
            our users. Other additions to The Blue Alliance include match
            prediction and analytics, hosting of CAD models, and The Blue
            Alliance Blog.
          </p>
          <p>
            Since 2022, The Blue Alliance has been a 501(c)(3) non-profit
            organization. We rely on community donations to pay for hosting
            costs.
          </p>

          <p>
            You can support The Blue Alliance or reach us with the following:
          </p>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" asChild>
              <a
                href="https://github.com/the-blue-alliance"
                target="_blank"
                rel="noreferrer"
              >
                Contribute on GitHub
              </a>
            </Button>
            <Button size="sm" asChild>
              <Link to="/donate">Donate with PayPal</Link>
            </Button>
            <Button size="sm" asChild>
              <Link to="/contact">Contact Us</Link>
            </Button>
          </div>
        </section>

        <section className="py-6 border-b">
          <h3 className="text-2xl font-medium mb-2">
            About <em>FIRST</em>
            <sup>®</sup>
          </h3>
          <p>
            <em>FIRST</em>
            <sup>®</sup> is the world’s leading youth-serving nonprofit
            advancing STEM education. Through a suite of inclusive, team-based
            robotics programs for ages 4-18 and backed by a global network of
            mentors, coaches, volunteers, alumni, and sponsors, FIRST has a
            proven impact on learning, interest, and skill-building inside and
            outside of the classroom.
          </p>
          <p>
            <em>FIRST</em>
            <sup>®</sup> Robotics Competition combines the excitement of sport
            with the rigors of science and technology. Under strict rules,
            limited time and resources, teams of high school students are
            challenged to build industrial-size robots to play a difficult field
            game in alliance with other teams, while they also fundraise to meet
            their goals, create a team identity, and advance respect and
            appreciation for STEM within the local community.
          </p>
          <Button size="sm" asChild>
            <a
              href="http://www.firstinspires.org"
              target="_blank"
              rel="noreferrer"
            >
              Join the movement
            </a>
          </Button>
        </section>

        <section className="py-6">
          <h3 className="text-2xl font-medium mb-2">Other community sites</h3>
          <p>
            Here are some other amazing resources that the <em>FIRST</em>{' '}
            community has to offer.
          </p>
          <ul className="list-inside">
            <li className="list-disc">
              <a href="https://www.chiefdelphi.com/" title="Chief Delphi">
                Chief Delphi
              </a>{' '}
              - The go-to fourm for FRC discussion
            </li>
            <li className="list-disc">
              <a href="https://frc.link/" title="FRC Links">
                FRC Links
              </a>{' '}
              - Easy access to specific FRC team and event pages
            </li>
            <li className="list-disc">
              <a href="https://www.statbotics.io/" title="Statbotics">
                Statbotics
              </a>{' '}
              - Unique FRC team and event performance comparisons
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
