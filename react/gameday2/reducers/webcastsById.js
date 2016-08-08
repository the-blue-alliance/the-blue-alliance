import { SET_WEBCASTS_RAW } from '../constants/ActionTypes'
import { getWebcastId } from '../utils/webcastUtils'

const getWebcastsFromRawWebcasts = (webcasts) => {
  const webcastsById = {};
  const specialWebcasts = webcasts.special_webcasts;
  const eventsWithWebcasts = webcasts.ongoing_events_w_webcasts;

  // First, deal with special webcasts
  // Sort order will be used later if we ever have to reconstruct the original
  // ordering of the webcasts
  let sortOrder = 0;
  for (const webcast of specialWebcasts) {
    const id = getWebcastId(webcast.key_name, 0);
    webcastsById[id] = {
      key: webcast.key_name,
      num: 0,
      id,
      name: webcast.name,
      type: webcast.type,
      channel: webcast.channel,
      sortOrder,
    };
    sortOrder++;
  }

  // Now, process normal event webcasts
  for (const event of eventsWithWebcasts) {
    let webcastNum = 0;
    for (const webcast of event.webcast) {
      let name = (event.short_name ? event.short_name : event.name);
      if (event.webcast.length > 1) {
        name = `${name} ${webcastNum + 1}`;
      }
      const id = getWebcastId(event.key, webcastNum);
      webcastsById[id] = {
        key: event.key,
        num: webcastNum,
        id,
        name,
        type: webcast.type,
        channel: webcast.channel,
      };
      webcastNum++;
    }
  }

  return webcastsById;
}

const webcastsById = (state = {}, action) => {
  switch (action.type) {
    case SET_WEBCASTS_RAW:
      return getWebcastsFromRawWebcasts(action.webcasts);
    default:
      return state;
  }
}

export default webcastsById
