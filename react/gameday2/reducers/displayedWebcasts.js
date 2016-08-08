import * as types from '../constants/ActionTypes'
import { MAX_SUPPORTED_VIEWS } from '../constants/LayoutConstants'

const addWebcastAtLocation = (displayedWebcasts, webcastId, location, maxSupportedViews) => {
  // Don't add the webcast if we couldn't possibly have a view to display it with
  const webcasts = displayedWebcasts.slice(0)
  if (location >= maxSupportedViews) {
    return webcasts
  }

  // If needed, expand the array
  while (location >= webcasts.length) {
    webcasts.push(null)
  }

  webcasts[location] = webcastId
  return webcasts
}

/**
 * Inserts a webcast at the next available location. If no location is available
 * in the given array, this function will expand up until the size specified by
 * maxSupportedViews. If the array would have to grow beyond that size, the
 * webcast ID is not added.
 */
const addWebcastAtNextAvailableLocation = (displayedWebcasts, webcastId, maxSupportedViews) => {
  const webcasts = displayedWebcasts.slice(0)
  for (let i = 0; i < webcasts.length; i++) {
    if (webcasts[i] == null) {
      webcasts[i] = webcastId
      return webcasts
    }
  }

  // There wasn't space for it in the original array. Try expanding it.
  if (displayedWebcasts.length >= maxSupportedViews) {
    // We can't expand the array any further. Don't add the webcast.
    return webcasts
  }

  webcasts.push(webcastId)
  return webcasts
}

const swapWebcasts = (displayedWebcasts, firstLocation, secondLocation) => {
  const webcasts = displayedWebcasts.slice(0)
  const temp = webcasts[firstLocation]
  webcasts[firstLocation] = webcasts[secondLocation]
  webcasts[secondLocation] = temp
  return webcasts
}

/**
 * If the specified webcast ID exists in displayedWebcasts, this function
 * replaces it with null.
 */
const removeWebcast = (displayedWebcasts, webcastId) => {
  const webcasts = displayedWebcasts.slice(0)
  for (let i = 0; i < webcasts.length; i++) {
    if (webcasts[i] === webcastId) {
      webcasts[i] = null
      return webcasts
    }
  }
  return webcasts
}

const displayedWebcasts = (state = [], action) => {
  switch (action.type) {
    case types.ADD_WEBCAST:
      return addWebcastAtNextAvailableLocation(state, action.webcastId, MAX_SUPPORTED_VIEWS)
    case types.ADD_WEBCAST_AT_LOCATION:
      return addWebcastAtLocation(state, action.webcastId, action.location, MAX_SUPPORTED_VIEWS)
    case types.SWAP_WEBCASTS:
      return swapWebcasts(state, action.firstLocation, action.secondLocation)
    case types.REMOVE_WEBCAST:
      return removeWebcast(state, action.webcastId)
    case types.RESET_WEBCASTS:
      return []
    default:
      return state
  }
}

export default displayedWebcasts
