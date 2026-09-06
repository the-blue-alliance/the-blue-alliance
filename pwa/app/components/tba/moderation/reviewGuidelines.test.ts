import { describe, expect, test } from 'vitest';

import { REVIEW_GUIDELINES } from '~/components/tba/moderation/reviewGuidelines';

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

describe.concurrent('REVIEW_GUIDELINES', () => {
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
