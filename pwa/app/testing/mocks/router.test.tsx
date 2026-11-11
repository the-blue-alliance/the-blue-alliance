import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import { Link } from '~/testing/mocks/router';

describe('Link', () => {
  test.each([
    { name: 'plain path', props: { to: '/events' }, href: '/events' },
    {
      name: 'path param',
      props: { to: '/event/$eventKey', params: { eventKey: '2026miket' } },
      href: '/event/2026miket',
    },
    {
      name: 'optional param with value',
      props: {
        to: '/team/$teamNumber/{-$year}',
        params: { teamNumber: '254', year: '2026' },
      },
      href: '/team/254/2026',
    },
    {
      name: 'optional param without value',
      props: {
        to: '/team/$teamNumber/{-$year}',
        params: { teamNumber: '254' },
      },
      href: '/team/254',
    },
    {
      name: 'search object',
      props: { to: '/match', search: { matchKey: '2026miket_qm1' } },
      href: '/match?matchKey=2026miket_qm1',
    },
    {
      name: 'hash',
      props: { to: '/team/254', hash: 'media' },
      href: '/team/254#media',
    },
  ])('builds the href for a $name', ({ props, href }) => {
    render(<Link {...props}>Go</Link>);

    expect(screen.getByRole('link', { name: 'Go' }).getAttribute('href')).toBe(
      href,
    );
  });

  test('keeps router-only props off the anchor', () => {
    render(
      <Link to="/" replace resetScroll={false} activeProps={{}}>
        Home
      </Link>,
    );

    expect(
      screen.getByRole('link', { name: 'Home' }).getAttributeNames(),
    ).toEqual(['href']);
  });
});
