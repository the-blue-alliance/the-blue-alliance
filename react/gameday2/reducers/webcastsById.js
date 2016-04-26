import { SET_WEBCASTS_RAW } from '../actions'
import { getWebcastId } from '../utils/webcastUtils'

const getWebcastsFromRawWebcasts = (webcasts) => {
  var webcastsById = {};
  var specialWebcasts = webcasts.special_webcasts;
  var eventsWithWebcasts = webcasts.ongoing_events_w_webcasts;

  // First, deal with special webcasts
  for (let webcast of specialWebcasts) {
    const id = getWebcastId(webcast.key_name, 0);
    webcastsById[id] = {
      'key': webcast.key_name,
      'num': 0,
      'id': id,
      'name': webcast.name,
      'type': webcast.type,
      'channel': webcast.channel
    };
  }

  // Now, process normal event webcasts
  for (let event of eventsWithWebcasts) {
    var webcastNum = 0;
    for (let webcast of event.webcast) {
      var name = (event.short_name ? event.short_name : event.name);
      if (event.webcast.length > 1) {
        name += (' ' + (webcastNum + 1));
      }
      const id = getWebcastId(event.key, webcastNum);
      webcastsById[id] = {
        'key': event.key,
        'num': webcastNum,
        'id': id,
        'name': name,
        'type': webcast.type,
        'channel': webcast.channel
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
