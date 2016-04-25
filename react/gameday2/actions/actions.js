export const SET_WEBCASTS_RAW = 'SET_WEBCASTS_RAW'

/**
 * Takes the JSON object from the server and produces a list of normalized
 * webcasts.
 */
export function setWebcastsRaw(webcasts) {
  return {
    type: SET_WEBCASTS_RAW,
    webcasts
  }
}
