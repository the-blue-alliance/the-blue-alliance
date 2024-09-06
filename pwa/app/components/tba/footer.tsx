import { Link } from '@remix-run/react';

import BiInfoCircleFill from '~icons/bi/info-circle-fill?width=16px&height=16px';

import andymark_logo from '~/images/andymark_logo.png';

export const Footer = () => {
  // TODO: Implement this as a backend/cache thing
  // Current time, formatted like "Aug. 23, 2024 at 11:57 AM"
  const render_time = new Date('1/1/2000').toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
    hour12: true,
  });

  return (
    <div className="flex flex-col space-y-3 p-5 text-center">
      <div className="justify-center">
        <hr className="w-full" />
      </div>
      <div>
        <div className="flex flex-row justify-center">
          <BiInfoCircleFill className="mx-1 mt-1" height={16} />

          <div className="mt-0">
            Data provided by the{' '}
            <Link
              to="https://frc-events.firstinspires.org/services/API"
              target="_blank"
              rel="noreferrer"
            >
              <em>FIRST</em>
              <sup>®</sup> Events API
            </Link>
          </div>
        </div>
      </div>

      <div className="flex grow justify-center">
        <hr className="w-full max-w-lg" />
      </div>

      <div>This page was generated on {render_time}</div>
      <div className="flex flex-row justify-center">
        Thanks to our platinum sponsor
        <Link
          to="https://www.andymark.com/"
          title="AndyMark"
          target="_blank"
          rel="noreferrer"
        >
          <img
            className="ml-1 mt-0.5"
            src={andymark_logo}
            alt="AndyMark"
            width="100"
          />
        </Link>
      </div>

      <div>
        The Blue Alliance is{' '}
        <Link
          to="https://github.com/the-blue-alliance/the-blue-alliance/"
          title="The Blue Alliance GitHub"
        >
          open source
        </Link>
        . Help improve it!
      </div>

      <div>
        <Link to="/about">About</Link>
        {' - '}
        <Link to="/add-data">Add Data</Link>
        {' - '}
        <Link to="/contact">Contact</Link>
        {' - '}
        <Link to="/donate">Donate</Link>
        {' - '}
        <Link to="/thanks">Thanks</Link>
        {' - '}
        <Link to="/apidocs">API</Link>
        {' - '}
        <Link to="/privacy">Privacy</Link>
      </div>

      <hr className="mt-1" />
    </div>
  );
};
