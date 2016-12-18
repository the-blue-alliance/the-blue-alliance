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
