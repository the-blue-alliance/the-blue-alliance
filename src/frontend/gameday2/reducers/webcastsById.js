"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.specialWebcastIds = exports.webcastsById = void 0;
const ActionTypes_1 = require("../constants/ActionTypes");
const webcastUtils_1 = require("../utils/webcastUtils");
const getWebcastsFromRawWebcasts = (webcasts) => {
  const webcastsById = {};
  const specialWebcasts = webcasts.special_webcasts;
  const specialWebcastIds = new Set();
  const eventsWithWebcasts = webcasts.ongoing_events_w_webcasts;
  // First, deal with special webcasts
  // Index will be used as sort order later if we ever have to reconstruct the
  // original ordering of the webcasts
  if (specialWebcasts) {
    specialWebcasts.forEach((webcast, index) => {
      const id = webcastUtils_1.getWebcastId(webcast.key_name, 0);
      // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      webcastsById[id] = {
        key: webcast.key_name,
        num: 0,
        id,
        name: webcast.name,
        type: webcast.type,
        channel: webcast.channel,
        file: webcast.file,
        sortOrder: index,
        status: webcast.status,
        streamTitle: webcast.stream_title,
        viewerCount: webcast.viewer_count,
      };
      specialWebcastIds.add(id);
    });
  }
  // Now, process normal event webcasts
  if (eventsWithWebcasts) {
    eventsWithWebcasts.forEach((event) => {
      event.webcasts.forEach((webcast, index) => {
        let name = event.short_name ? event.short_name : event.name;
        if (event.webcasts.length > 1) {
          name = `${name} ${index + 1}`;
        }
        const id = webcastUtils_1.getWebcastId(event.key, index);
        // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        webcastsById[id] = {
          key: event.key,
          num: index,
          id,
          name,
          type: webcast.type,
          channel: webcast.channel,
          file: webcast.file,
          status: webcast.status,
          streamTitle: webcast.stream_title,
          viewerCount: webcast.viewer_count,
        };
      });
    });
  }
  const allWebcasts = {
    webcastsById,
    specialWebcastIds,
  };
  return allWebcasts;
};
const webcastsById = (state = {}, action) => {
  switch (action.type) {
    case ActionTypes_1.SET_WEBCASTS_RAW:
      return getWebcastsFromRawWebcasts(action.webcasts).webcastsById;
    default:
      return state;
  }
};
exports.webcastsById = webcastsById;
const specialWebcastIds = (state = {}, action) => {
  switch (action.type) {
    case ActionTypes_1.SET_WEBCASTS_RAW:
      return getWebcastsFromRawWebcasts(action.webcasts).specialWebcastIds;
    default:
      return state;
  }
};
exports.specialWebcastIds = specialWebcastIds;
