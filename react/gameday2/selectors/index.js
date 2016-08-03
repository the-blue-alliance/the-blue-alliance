import { createSelector } from 'reselect'

const getWebcastsById = (state) => state.webcastsById

export const getWebcastIds = createSelector(
  [ getWebcastsById ],
  (webcastsById) => {
    let webcastIds = []
    for (let key in webcastsById) {
      webcastIds.push(key)
    }
    return webcastIds
  }
)

export const getWebcastIdsInDisplayOrder = createSelector(
  [ getWebcastsById ],
  (webcastsById) => {
    let displayOrderWebcastIds = []
    console.log('webcasts by id')
    console.log(webcastsById)

    // Flatten the map of id->webcast to an array of webcast objects
    let webcastsArray = [];
    for (let key in webcastsById) {
      if(webcastsById.hasOwnProperty(key)) {
        webcastsArray.push(webcastsById[key])
      }
    }

    // First, select all webcasts that have a designated sort order
    // This is usually assigned for all special webcasts; we want to maintain
    // the order the server provides them in

    let orderedWebcasts = webcastsArray.filter(webcast => webcast.hasOwnProperty('sortOrder'))
    for (let webcast of orderedWebcasts) {
      displayOrderWebcastIds.push(webcast.id)
    }

    // Next, sort all webcasts without an explicit sort order and sort them by
    // webcast name

    let unorderedWebcasts = webcastsArray.filter(webcast => !webcast.hasOwnProperty('sortOrder'))
    let sortedUnorderedWebcasts = unorderedWebcasts.sort((a, b) => a.name.localeCompare(b.name))
    for (let webcast of sortedUnorderedWebcasts) {
      displayOrderWebcastIds.push(webcast.id)
    }

    return displayOrderWebcastIds
  }
)
