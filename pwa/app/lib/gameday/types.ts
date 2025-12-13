import type { Webcast } from '~/api/tba/read';

/**
 * Supported webcast types
 */
export type WebcastType = Webcast['type'];

/**
 * Firebase RTDB structure for webcasts.
 * This matches the backend Webcast model with WebcastOnlineStatus fields.
 */
export interface FirebaseWebcast {
  type: WebcastType;
  channel: string;
  file?: string;
  date?: string;
  // Live status fields populated by WebcastOnlineHelper
  status?: 'unknown' | 'online' | 'offline';
  stream_title?: string | null;
  viewer_count?: number | null;
}

/**
 * Firebase RTDB structure for special webcasts.
 * Extends FirebaseWebcast with additional name/key fields.
 */
export interface FirebaseSpecialWebcast extends FirebaseWebcast {
  key_name: string;
  name: string;
}

/**
 * Firebase RTDB structure for live events
 */
export interface FirebaseLiveEvent {
  key: string;
  name: string;
  short_name?: string;
  webcasts: FirebaseWebcast[];
}

/**
 * Extended webcast information with metadata from the event
 */
export interface WebcastWithMeta {
  /** Unique identifier for this webcast (eventKey-num format) */
  id: string;
  /** Display name for the webcast */
  name: string;
  /** Webcast data from Firebase */
  webcast: FirebaseWebcast;
  /** Whether this is a special webcast (vs regular event webcast) */
  isSpecial: boolean;
}

/**
 * Get a unique ID for a webcast
 */
export function getWebcastId(eventKey: string, num: number): string {
  return `${eventKey}-${num}`;
}
