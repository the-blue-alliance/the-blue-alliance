/* eslint-disable max-len */
import { createSelector } from 'reselect'

const getWebcastsById = (state) => state.webcastsById

export const getWebcastIds = createSelector(
  [getWebcastsById],
  (webcastsById) => {
    const webcastIds = []
    Object.keys(webcastsById)
      .filter((key) => ({}.hasOwnProperty.call(webcastsById, key)))
      .forEach((key) => webcastIds.push(key))
    return webcastIds
  }
)

export const getWebcastIdsInDisplayOrder = createSelector(
  [getWebcastsById],
  (webcastsById) => {
    const displayOrderWebcastIds = []

    // Flatten the map of id->webcast to an array of webcast objects
    const webcastsArray = []
    Object.keys(webcastsById)
      .filter((key) => ({}.hasOwnProperty.call(webcastsById, key)))
      .forEach((key) => webcastsArray.push(webcastsById[key]))

    // First, select all webcasts that have a designated sort order
    // This is usually assigned for all special webcasts; we want to maintain
    // the order the server provides them in

    const orderedWebcasts = webcastsArray.filter((webcast) => ({}.hasOwnProperty.call(webcast, 'sortOrder')))
    const sortedOrderedWebcasts = orderedWebcasts.sort((a, b) => a.sortOrder > b.sortOrder)
    sortedOrderedWebcasts.forEach((webcast) => displayOrderWebcastIds.push(webcast.id))

    // Next, sort all webcasts without an explicit sort order and sort them by
    // webcast name

    const unorderedWebcasts = webcastsArray.filter((webcast) => !({}.hasOwnProperty.call(webcast, 'sortOrder')))
    const sortedUnorderedWebcasts = unorderedWebcasts.sort((a, b) => a.name.localeCompare(b.name))
    sortedUnorderedWebcasts.forEach((webcast) => displayOrderWebcastIds.push(webcast.id))

    return displayOrderWebcastIds
  }
)

export const getChats = (state) => state.chats

export const getChatsInDisplayOrder = createSelector(
  [getChats],
  (chats) => {
    const displayOrderChats = []
    Object.keys(chats.chats)
      .filter((key) => ({}.hasOwnProperty.call(chats.chats, key)))
      .forEach((key) => displayOrderChats.push(chats.chats[key]))

    return displayOrderChats.sort((a, b) => a.name.localeCompare(b.name))
  }
)

export const getFireduxData = (state) => state.firedux.data

export const getEventKey = (state, props) => props.webcast.key

export const getEventMatches = createSelector(
  [getFireduxData, getEventKey],
  (fireduxData, eventKey) => {
    const compLevelsPlayOrder = {
      qm: 1,
      ef: 2,
      qf: 3,
      sf: 4,
      f: 5,
    }
    function calculateOrder(match) {
      // let time = 9999999999
      // if (match.r !== -1 && match.b !== -1) {
      //   time = 0
      // }
      // if (match.pt) {
      //   time = match.pt
      // }
      return (compLevelsPlayOrder[match.c] * 100000) + (match.m * 100) + match.s
    }

    const matches = []
    if (fireduxData &&
        fireduxData.e &&
        fireduxData.e[eventKey] &&
        fireduxData.e[eventKey].m) {
      Object.keys(fireduxData.e[eventKey].m).forEach((shortKey) => {
        const match = Object.assign({}, fireduxData.e[eventKey].m[shortKey])
        match.key = `${eventKey}_${shortKey}`
        match.shortKey = shortKey
        matches.push(match)
      })

      matches.sort((match1, match2) => calculateOrder(match1) - calculateOrder(match2))
    }
    return matches
  }
)

export const getTickerMatches = createSelector(
  [getFireduxData, getEventMatches],
  (fireduxData, matches) => {
    let lastMatch = null
    let selectedMatches = []
    matches.forEach((match) => {
      if (match.r === -1 || match.b === -1) {
        selectedMatches.push(match)
      } else {
        lastMatch = match
        selectedMatches = [] // Reset selectedMatches if matches get skipped
      }
    })

    // Prepend lastMatch to matches
    if (lastMatch != null) {
      selectedMatches.unshift(lastMatch)
    }

    return selectedMatches
  }
)

export const getCurrentMatchState = createSelector(
  [getFireduxData, getEventKey],
  (fireduxData, eventKey) => {
    if (fireduxData &&
        fireduxData.le &&
        fireduxData.le[eventKey]) {
      return fireduxData.le[eventKey]
    }
    return null
  }
)
