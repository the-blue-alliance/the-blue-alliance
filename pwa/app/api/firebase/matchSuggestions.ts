import type { FromSchema } from 'json-schema-to-ts';

import { matchSuggestionsSchema } from '~/api/firebase/matchSuggestions.schema.gen';

/**
 * The GameDay match suggestion feed, at the Firebase `match_suggestions` node.
 *
 * `keepDefaultedPropertiesOptional` is required: json-schema-to-ts otherwise
 * types a property with a schema default as always present, but the Realtime
 * Database drops null children on write, so those keys arrive absent.
 */
export type MatchSuggestions = FromSchema<
  typeof matchSuggestionsSchema,
  { keepDefaultedPropertiesOptional: true }
>;
/**
 * Sort by `r` (rank) -- the feed is keyed by match key, so snapshot order is
 * meaningless. Per-suggestion keys are terse because the Realtime Database
 * bills per byte.
 */
export type MatchSuggestion = NonNullable<
  MatchSuggestions['suggestions']
>[string];
export type MatchSuggestionComponents = MatchSuggestion['c'];
export type CompLevel = MatchSuggestion['cl'];
