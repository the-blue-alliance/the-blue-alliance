import { Link } from '@remix-run/react';

import BiInfoCircleFill from '~icons/bi/info-circle-fill';

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
    <div className="p-5 flex flex-col justify-center">
      <div className="justify-center">
        <hr className="w-full my-1" />

        <div className="flex flex-row justify-center">
          <BiInfoCircleFill className="m-2" />

          <div className="mt-1.5">
            Data provided by the{' '}
            <Link
              to="https://frc-events.firstinspires.org/services/API"
              target="_blank"
            >
              <em>FIRST</em>
              <sup>®</sup> Events API
            </Link>
          </div>
        </div>
      </div>
      {/* <div> */}
      {/* style="overflow: hidden;" */}
      {/* <div
            className="fb-like"
            data-href="https://www.facebook.com/thebluealliance"
            data-width="450"
            data-layout="standard"
            data-action="like"
            data-show-faces="true"
            data-share="true"
          ></div> */}
      {/* </div> */}

      <div className="flex grow justify-center my-1">
        <hr className="w-full max-w-lg" />
      </div>

      {/* {% if render_time %} */}
      <div className="text-center">
        <p>This page was generated on {render_time}</p>
      </div>
      {/* {% endif %} */}
      {/* <div><p>Thanks to our platinum sponsor <a href="https://www.andymark.com/" title="AndyMark"><img src="/images/andymark_logo.png" alt="AndyMark" width="100" /></a></p></div> */}
      {/* <div>
          <p>
            The Blue Alliance is{' '}
            <a
              href="https://github.com/the-blue-alliance/the-blue-alliance/"
              title="The Blue Alliance GitHub"
            >
              open source
            </a>
            . Help improve it!
          </p>
        </div> */}
      <div className="text-center">
        <a href="/about">About</a>
        {' - '}
        <a href="/add-data">Add Data</a>
        {' - '}
        <a href="/contact">Contact</a>
        {' - '}
        <a href="/donate">Donate</a>
        {' - '}
        <a href="/thanks">Thanks</a>
        {' - '}
        <a href="/apidocs">API</a>
        {' - '}
        <a href="/privacy">Privacy</a>
      </div>

      <hr className="mt-1" />
    </div>
  );
};
