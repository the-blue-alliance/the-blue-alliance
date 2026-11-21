import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';

import {
  REVIEW_GUIDELINES,
  ReviewGuidelines,
} from '~/components/tba/moderation/reviewGuidelines';

const VALID_SUGGESTION_TYPES = [
  'match',
  'media',
  'social-media',
  'robot',
  'event_media',
  'event',
  'offseason-event',
  'api_auth_access',
];

describe('REVIEW_GUIDELINES', () => {
  test('covers the types that have guidance in the web review templates', () => {
    expect(Object.keys(REVIEW_GUIDELINES).sort()).toEqual([
      'api_auth_access',
      'event_media',
      'media',
      'offseason-event',
    ]);
  });

  test('only uses valid suggestion type slugs', () => {
    for (const type of Object.keys(REVIEW_GUIDELINES)) {
      expect(VALID_SUGGESTION_TYPES).toContain(type);
    }
  });

  test('every set has a title, dos, and donts', () => {
    for (const sets of Object.values(REVIEW_GUIDELINES)) {
      expect(sets.length).toBeGreaterThan(0);
      for (const set of sets) {
        expect(set.title).toBeTruthy();
        expect(set.dos.length).toBeGreaterThan(0);
        expect(set.donts.length).toBeGreaterThan(0);
      }
    }
  });

  test('team media has both video and image guideline sets', () => {
    expect(REVIEW_GUIDELINES.media.map((set) => set.title)).toEqual([
      'Video Approval Guidelines',
      'Image Approval Guidelines',
    ]);
  });
});

describe('ReviewGuidelines', () => {
  test('lists what to approve and reject for each guideline set', () => {
    render(<ReviewGuidelines suggestionType="media" />);

    expect(
      screen.getAllByRole('heading').map((heading) => heading.textContent),
    ).toEqual(['Video Approval Guidelines', 'Image Approval Guidelines']);
    expect(screen.getAllByText('Do approve:')).toHaveLength(2);
    expect(screen.getByText('Robot reveal')).toBeTruthy();
    expect(screen.getByText('GIFs')).toBeTruthy();
  });

  test('shows webcast formatting protips for events', () => {
    const { container } = render(<ReviewGuidelines suggestionType="event" />);

    expect(
      screen.getByRole('heading', { name: 'Webcast Formatting Protips' }),
    ).toBeTruthy();
    expect(
      [...container.querySelectorAll('dt')].map((dt) => dt.textContent),
    ).toEqual(['Livestream', 'Ustream', 'DaCast']);
    expect(screen.getByText('_c_').tagName).toBe('CODE');
  });

  test('renders nothing for types without guidance', () => {
    const { container } = render(<ReviewGuidelines suggestionType="match" />);

    expect(container.innerHTML).toBe('');
  });
});
