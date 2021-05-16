"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getCurrentMatchState =
  exports.getTickerMatches =
  exports.getEventMatches =
  exports.getEventKey =
  exports.getFireduxData =
  exports.getChatsInDisplayOrder =
  exports.getChats =
  exports.getWebcastIdsInDisplayOrder =
  exports.getWebcastIds =
    void 0;
/* eslint-disable max-len */
const reselect_1 = require("reselect");
const getWebcastsById = (state) => state.webcastsById;
exports.getWebcastIds = reselect_1.createSelector(
  [getWebcastsById],
  (webcastsById) => {
    const webcastIds = [];
    Object.keys(webcastsById)
      .filter((key) => ({}.hasOwnProperty.call(webcastsById, key)))
      .forEach((key) => webcastIds.push(key));
    return webcastIds;
  }
);
exports.getWebcastIdsInDisplayOrder = reselect_1.createSelector(
  [getWebcastsById],
  (webcastsById) => {
    const displayOrderWebcastIds = [];
    // Flatten the map of id->webcast to an array of webcast objects
    const webcastsArray = [];
    Object.keys(webcastsById)
      .filter((key) => ({}.hasOwnProperty.call(webcastsById, key)))
      .forEach((key) => webcastsArray.push(webcastsById[key]));
    // First, select all webcasts that have a designated sort order
    // This is usually assigned for all special webcasts; we want to maintain
    // the order the server provides them in
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'webcast' implicitly has an 'any' type.
    const orderedWebcasts = webcastsArray.filter((webcast) =>
      ({}.hasOwnProperty.call(webcast, "sortOrder"))
    );
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'a' implicitly has an 'any' type.
    const sortedOrderedWebcasts = orderedWebcasts.sort((a, b) =>
      a.sortOrder > b.sortOrder ? 1 : -1
    );
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'webcast' implicitly has an 'any' type.
    sortedOrderedWebcasts.forEach((webcast) =>
      displayOrderWebcastIds.push(webcast.id)
    );
    // Next, sort all webcasts without an explicit sort order and sort them by
    // webcast name
    const unorderedWebcasts = webcastsArray.filter(
      // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'webcast' implicitly has an 'any' type.
      (webcast) => !{}.hasOwnProperty.call(webcast, "sortOrder")
    );
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'a' implicitly has an 'any' type.
    const sortedUnorderedWebcasts = unorderedWebcasts.sort((a, b) =>
      a.name.localeCompare(b.name)
    );
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'webcast' implicitly has an 'any' type.
    sortedUnorderedWebcasts.forEach((webcast) =>
      displayOrderWebcastIds.push(webcast.id)
    );
    return displayOrderWebcastIds;
  }
);
const getChats = (state) => state.chats;
exports.getChats = getChats;
exports.getChatsInDisplayOrder = reselect_1.createSelector(
  [exports.getChats],
  (chats) => {
    const displayOrderChats = [];
    Object.keys(chats.chats)
      .filter((key) => ({}.hasOwnProperty.call(chats.chats, key)))
      .forEach((key) => displayOrderChats.push(chats.chats[key]));
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'a' implicitly has an 'any' type.
    return displayOrderChats.sort((a, b) => a.name.localeCompare(b.name));
  }
);
const getFireduxData = (state) => state.firedux.data;
exports.getFireduxData = getFireduxData;
const getEventKey = (state, props) => props.webcast.key;
exports.getEventKey = getEventKey;
exports.getEventMatches = reselect_1.createSelector(
  [exports.getFireduxData, exports.getEventKey],
  (fireduxData, eventKey) => {
    const compLevelsPlayOrder = {
      qm: 1,
      ef: 2,
      qf: 3,
      sf: 4,
      f: 5,
    };
    function calculateOrder(match) {
      // let time = 9999999999
      // if (match.r !== -1 && match.b !== -1) {
      //   time = 0
      // }
      // if (match.pt) {
      //   time = match.pt
      // }
      // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      return compLevelsPlayOrder[match.c] * 100000 + match.m * 100 + match.s;
    }
    const matches = [];
    if (
      fireduxData &&
      fireduxData.e &&
      fireduxData.e[eventKey] &&
      fireduxData.e[eventKey].m
    ) {
      Object.keys(fireduxData.e[eventKey].m).forEach((shortKey) => {
        const match = Object.assign({}, fireduxData.e[eventKey].m[shortKey]);
        match.key = `${eventKey}_${shortKey}`;
        match.shortKey = shortKey;
        matches.push(match);
      });
      matches.sort(
        // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'match1' implicitly has an 'any' type.
        (match1, match2) => calculateOrder(match1) - calculateOrder(match2)
      );
    }
    return matches;
  }
);
exports.getTickerMatches = reselect_1.createSelector(
  [exports.getFireduxData, exports.getEventMatches],
  (fireduxData, matches) => {
    let lastMatch = null;
    let selectedMatches = [];
    // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'match' implicitly has an 'any' type.
    matches.forEach((match) => {
      if (match.r === -1 || match.b === -1) {
        selectedMatches.push(match);
      } else {
        lastMatch = match;
        selectedMatches = []; // Reset selectedMatches if matches get skipped
      }
    });
    // Prepend lastMatch to matches
    if (lastMatch != null) {
      selectedMatches.unshift(lastMatch);
    }
    return selectedMatches;
  }
);
exports.getCurrentMatchState = reselect_1.createSelector(
  [exports.getFireduxData, exports.getEventKey],
  (fireduxData, eventKey) => {
    if (fireduxData && fireduxData.le && fireduxData.le[eventKey]) {
      return fireduxData.le[eventKey];
    }
    return null;
  }
);
