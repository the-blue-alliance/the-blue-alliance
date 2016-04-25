import { SET_WEBCASTS_RAW } from '../actions/actions'
import { getWebcastId } from '../utils/webcastUtils'

/**
 * Generates a list of webcast ids from raw webcast data.
 * The data is ordered as follows:
 *
 * 1. All special webcasts come first, in the order that they are provided
 * 2. Event webcasts come second; they are sorted first by event name and then
 *    by number
 */
const getWebcastIdsFromRawWebcasts = (webcasts) => {
  var outWebcasts = []
  var specialWebcasts = webcasts.special_webcasts
  var eventsWithWebcasts = webcasts.ongoing_events_w_webcasts

  // First, deal with special webcasts
  for (let webcast of specialWebcasts) {
    const id = webcast.key_name + 0
    outWebcasts.push(getWebcastId(webcast.key_name, 0))
  }

  // Now, process normal event webcasts
  // This block will generate an array like this, which we will then sort by
  // name:
  //
  // [ { name: "EventA 1", id: "eventa-0"}, { name: "EventA2", id: "eventa-1"}]
  let eventWebcasts = [];
  for (let event of eventsWithWebcasts) {
    let webcastNum = 0
    for (let webcast of event.webcast) {
      let name = (event.short_name ? event.short_name : event.name)
      if (event.webcast.length > 1) {
        name += (' ' + (webcastNum + 1))
      }
      const id = getWebcastId(event.key, webcastNum)
      eventWebcasts.push({
        name,
        id
      })
      webcastNum++;
    }
  }

  // Sort event webcasts by webcast name
  eventWebcasts.sort((a, b) => a.name.localeCompare(b.name));

  // Merge event webcast ids into main webcast list
  for (let webcast of eventWebcasts) {
    outWebcasts.push(webcast.id);
  }

  return outWebcasts;
}

const webcasts = (state = [], action) => {
  switch (action.type) {
    case SET_WEBCASTS_RAW:
    return getWebcastIdsFromRawWebcasts(action.webcasts);
    default:
    return state;
  }
}

export default webcasts
