import { Link } from '@remix-run/react';
import { Button } from '~/components/ui/button';

export default function About(): JSX.Element {
  return (
    <>
      <div className="flex flex-col divide-y [&_*]:mt-4">
        <div>
          <h1 className="text-3xl font-medium">About Us</h1>
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
          <Button asChild>
            <a href="https://github.com/the-blue-alliance">
              Contribute on GitHub!
            </a>
          </Button>
          <Button asChild>
            <Link to="/donate">Donate with PayPal</Link>
          </Button>
          <Button asChild>
            <Link to="/contact">Contact Us!</Link>
          </Button>
        </div>

        <div>
          <h3 className="text-2xl">
            About <em>FIRST</em> and <em>FIRST</em> Robotics Competition
          </h3>
          <p>
            <a href="http://www.firstinspires.org/">
              {' '}
              <em>FIRST</em>
            </a>{' '}
            (For Inspiration and Recognition of Science and Technology) is a
            non-profit organization with the mission of inspiring young people
            to be science and technology leaders. With programs that involve
            students from kindergarten through high school, <em>FIRST</em> has
            become a world-wide phenomenon with teams from all six inhabited
            continents.
          </p>
          <p>
            The{' '}
            <a href="https://www.firstinspires.org/robotics/frc">
              <em>FIRST</em> Robotics Competition (FRC)
            </a>{' '}
            gives high school students and their adult mentors the opportunity
            to work and create together to solve a common problem. Each{' '}
            <em>FIRST</em> Robotics Competition season culminates with local and
            regional events where qualifying teams compete for awards and a spot
            in the <em>FIRST</em> Championship.
          </p>

          <div className="flex">
            <img
              src="https://www.firstinspires.org/sites/default/files/uploads/resource_library/brand/thumbnails/FIRST-V.png"
              alt="FIRST' Logo"
              className="h-16 w-auto"
            />

            <blockquote>
              <p>
                <em>
                  &quot;To transform our culture by creating a world where
                  science and technology are celebrated and where young people
                  dream of becoming science and technology leaders.&quot;
                </em>
              </p>
              <small>
                Dean Kamen, <em>FIRST</em> Founder (
                <a href="http://www.firstinspires.org/about/vision-and-mission">
                  <em>FIRST</em> Vision
                </a>
                )
              </small>
            </blockquote>
          </div>
        </div>

        <div>
          <h3 className="text-2xl">Other community sites</h3>
          <p>
            Here are some other amazing resources that the <em>FIRST</em>{' '}
            community has to offer.
          </p>

          <ul>
            <li className="list-disc">
              <p>
                <a href="https://www.chiefdelphi.com/" title="Chief Delphi">
                  Chief Delphi
                </a>{' '}
                - The go-to fourm for FRC discussion
              </p>
            </li>
            <li className="list-disc">
              <p>
                <a href="https://frc.link/" title="FRC Links">
                  FRC Links
                </a>{' '}
                - Easy access to specific FRC team and event pages
              </p>
            </li>
            <li className="list-disc">
              <p>
                <a href="https://www.statbotics.io/" title="Statbotics">
                  Statbotics
                </a>{' '}
                - Unique FRC team and event performance comparisons
              </p>
            </li>
          </ul>
        </div>
      </div>
    </>
  );
}
