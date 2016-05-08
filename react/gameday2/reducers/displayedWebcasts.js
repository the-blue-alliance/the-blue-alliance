import * as types from '../constants/ActionTypes'
import { MAX_SUPPORTED_VIEWS } from '../constants/LayoutConstants'

const addWebcastAtLocation = (displayedWebcasts, webcastId, location, maxSupportedViews) => {
  // Don't add the webcast if we couldn't possibly have a view to display it with
  if (location >= maxSupportedViews) {
    return
  }

  // If needed, expand the array
  while (location >= displayedWebcasts.length) {
    displayedWebcasts.push(null)
  }

  displayedWebcasts[location] = webcastId
}

/**
 * Inserts a webcast at the next available location. If no location is available
 * in the given array, this function will expand up until the size specified by
 * maxSupportedViews. If the array would have to grow beyond that size, the
 * webcast ID is not added.
 */
const addWebcastAtNextAvailableLocation = (displayedWebcasts, webcastId, maxSupportedViews) => {
  for (let i = 0; i < displayedWebcasts.length; i++) {
    if (displayedWebcasts[i] == undefined) {
      displayedWebcasts[i] = webcastId
      return
    }
  }

  // There wasn't space for it in the original array. Try expanding it.
  if (displayedWebcasts.length >= maxSupportedViews) {
    // We can't expand the array any further. Don't add the webcast.
    return
  }

  displayedWebcasts.push(webcastId)
}

const swapWebcasts = (displayedWebcasts, firstLocation, secondLocation) => {
  let temp = displayedWebcasts[firstLocation]
  displayedWebcasts[firstLocation] = displayedWebcasts[secondLocation]
  displayedWebcasts[secondLocation] = temp
}

/**
 * If the specified webcast ID exists in displayedWebcasts, this function
 * replaces it with null.
 */
const removeWebcast = (displayedWebcasts, webcastId) => {
  for (let i = 0; i < displayedWebcasts.length; i++) {
    if (displayedWebcasts[i] == webcastId) {
      displayedWebcasts[i] = null
      return
    }
  }
}

const displayedWebcasts = (state = [], action) => {
  let webcasts = null;
  switch (action.type) {
    case types.ADD_WEBCAST:
      webcasts = state.slice(0)
      addWebcastAtNextAvailableLocation(webcasts, action.webcastId, MAX_SUPPORTED_VIEWS)
      return webcasts
    case types.ADD_WEBCAST_AT_LOCATION:
      webcasts = state.slice(0)
      addWebcastAtLocation(webcasts, action.webcastId, action.location, MAX_SUPPORTED_VIEWS)
      return webcasts
    case types.SWAP_WEBCASTS:
      webcasts = state.slice(0)
      swapWebcasts(webcasts, action.firstLocation, action.secondLocation)
      return webcasts
    case types.REMOVE_WEBCAST:
      webcasts = state.slice(0)
      removeWebcast(webcasts, action.webcastId)
      return webcasts
    case types.RESET_WEBCASTS:
      return []
    default:
      return state
  }
}

export default displayedWebcasts
