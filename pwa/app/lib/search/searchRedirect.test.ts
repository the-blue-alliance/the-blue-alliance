import { describe, expect, it } from 'vitest';

import { SearchIndex } from '~/api/tba/read';
import { getSearchRedirect } from '~/lib/search/searchRedirect';

// Mock search index data for testing
const mockSearchIndex: SearchIndex = {
  teams: [
    { key: 'frc254', nickname: 'The Cheesy Poofs' },
    { key: 'frc604', nickname: 'Quixilver' },
    { key: 'frc1678', nickname: 'Citrus Circuits' },
  ],
  events: [
    { key: '2024casj', name: 'Silicon Valley Regional' },
    { key: '2024mil', name: 'Milstein' },
    { key: '2024cmptx', name: 'Einstein Field' },
  ],
};

describe('getSearchRedirect', () => {
  describe('team searches', () => {
    it('should redirect to team by number', () => {
      const result = getSearchRedirect(mockSearchIndex, '254');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/254');
    });

    it('should redirect to team by key with frc prefix', () => {
      const result = getSearchRedirect(mockSearchIndex, 'frc254');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/254');
    });

    it('should redirect to team by full nickname', () => {
      const result = getSearchRedirect(mockSearchIndex, 'Cheesy Poofs');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/254');
    });

    it('should redirect to team by partial nickname', () => {
      const result = getSearchRedirect(mockSearchIndex, 'Cheesy');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/254');
    });

    it('should redirect to team 604 by nickname', () => {
      const result = getSearchRedirect(mockSearchIndex, 'Quixilver');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/604');
    });
  });

  describe('event searches', () => {
    it('should redirect to event by key', () => {
      const result = getSearchRedirect(mockSearchIndex, '2024casj');
      expect(result.type).toBe('event');
      expect(result.path).toBe('/event/2024casj');
    });

    it('should redirect to event by full name', () => {
      const result = getSearchRedirect(
        mockSearchIndex,
        'Silicon Valley Regional',
      );
      expect(result.type).toBe('event');
      expect(result.path).toBe('/event/2024casj');
    });

    it('should redirect to event by partial name', () => {
      const result = getSearchRedirect(mockSearchIndex, 'Silicon Valley');
      expect(result.type).toBe('event');
      // Should match either 2024casj or 2024casjcmp, both are valid
      expect(result.path).toMatch(/^\/event\/2024casj/);
    });

    it('should redirect to event 2024mil', () => {
      const result = getSearchRedirect(mockSearchIndex, '2024mil');
      expect(result.type).toBe('event');
      expect(result.path).toBe('/event/2024mil');
    });
  });

  describe('edge cases', () => {
    it('should return no-results for empty query', () => {
      const result = getSearchRedirect(mockSearchIndex, '');
      expect(result.type).toBe('no-results');
      expect(result.path).toBeUndefined();
    });

    it('should return no-results for whitespace-only query', () => {
      const result = getSearchRedirect(mockSearchIndex, '   ');
      expect(result.type).toBe('no-results');
      expect(result.path).toBeUndefined();
    });

    it('should return no-results for query with no matches', () => {
      const result = getSearchRedirect(mockSearchIndex, 'xyzabc123');
      expect(result.type).toBe('no-results');
      expect(result.path).toBeUndefined();
    });

    it('should preserve original query in result', () => {
      const result = getSearchRedirect(mockSearchIndex, '  254  ');
      expect(result.query).toBe('  254  ');
    });
  });

  describe('priority logic', () => {
    it('should prefer team when both team and event match', () => {
      // When searching for something that could match both, teams should win
      const result = getSearchRedirect(mockSearchIndex, '604');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/604');
    });

    it('should return team when only team matches', () => {
      const emptyEvents: SearchIndex = {
        teams: mockSearchIndex.teams,
        events: [],
      };
      const result = getSearchRedirect(emptyEvents, '254');
      expect(result.type).toBe('team');
      expect(result.path).toBe('/team/254');
    });

    it('should return event when only event matches', () => {
      const emptyTeams: SearchIndex = {
        teams: [],
        events: mockSearchIndex.events,
      };
      const result = getSearchRedirect(emptyTeams, '2024casj');
      expect(result.type).toBe('event');
      expect(result.path).toBe('/event/2024casj');
    });
  });
});
