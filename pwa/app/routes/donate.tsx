import { Link } from '@remix-run/react';
import { Button } from '~/components/ui/button';

export default function Contact(): JSX.Element {
  return (
    <>
      <div className="flex flex-col divide-y [&_*]:mt-4">
        <div>
          <h1 className="text-3xl font-medium">Donate</h1>
          <p>
            The Blue Alliance relies on the volunteer effort of people who
            contribute code, moderate data submissions, and upload match videos
            and robot photos. Thank you to everyone who has been involved since
            TBA was started in 2006.
          </p>
          <p>
            In 2022, The Blue Alliance formally became a non-profit
            organization. This enables us to get discounts on some services that
            keep the site running, and means that donations to The Blue Alliance
            are tax deductible. We spend around $4,000 per year, almost entirely
            on Google Cloud Platform hosting, to keep the site up and running.
          </p>
          <p>
            The best donations are monthly contributions, which help us budget
            for the future. If we get to a place where we are receiving much
            more in donations than our operating costs, we&apos;ll explore
            hiring a summer intern.
          </p>
          <p>The Blue Alliance&apos;s EIN is 88-3600243.</p>
          <p>
            If you&apos;d like to make a large donation, or a
            capital-gains-tax-advantaged donation through a donor advised fund,
            please <Link to="/contact">contact us</Link> and we&apos;ll be in
            touch!
          </p>
          <p>
            The Blue Alliance would like to{' '}
            <Link to="/thanks">thank all of our sponsors</Link> whose generous
            support has made it possible to keep the site running.
          </p>
          <Button asChild>
            <a href="https://www.paypal.com/donate/?hosted_button_id=RNFK8Y7FU9VX8">
              Donate on PayPal!
            </a>
          </Button>
        </div>
      </div>
    </>
  );
}
