import * as types from '../constants/ActionTypes'
import { MAX_SUPPORTED_VIEWS, NUM_VIEWS_FOR_LAYOUT } from '../constants/LayoutConstants'

// Position map maps from a location index in the grid to a position in the DOM ordering

const positionMap = []
const domOrder = []
for (let i = 0; i < MAX_SUPPORTED_VIEWS; i++) {
  domOrder.push(null)
  positionMap.push(-1)
}

const defaultState = {
  layoutId: 0,
  layoutSet: false,
  displayed: [],
  domOrder,
  positionMap,
}

const addWebcastAtLocation = (state, webcastId, location, maxSupportedViews) => {
  if (location < 0 || location >= maxSupportedViews) {
    return state
  }

  let {
    displayed,
    domOrder,
    positionMap,
  } = state

  displayed = displayed.slice(0)
  domOrder = domOrder.slice(0)
  positionMap = positionMap.slice(0)

  // See if there's already a webcast at this location
  let existingIndex = positionMap[location]
  if (existingIndex >= 0) {
    // There's already a webcast at this position with a corresponding DOM element
    const oldId = domOrder[existingIndex]
    domOrder[existingIndex] = webcastId

    // Update the displayed array
    let displayedIndex = displayed.indexOf(oldId)
    if (index >= 0) {
      displayed[index] = webcastId
    } else {
      displayed.push(webcastId)
    }
  } else {
    // There isn't a webcast at this position, so we'll need to find room in the DOM
    // for it
    for (let i = 0; i < domOrder.length; i++) {
      if (domOrder[i] == null) {
        // We found an opening!
        domOrder[i] = webcastId
        positionMap[location] = i
        break
      }
    }

    displayed.push(webcastId)
  }

  return trimToLayout(Object.assign({}, state, {
    displayed,
    domOrder,
    positionMap,
  }))
}

const swapWebcasts = (state, firstLocation, secondLocation) => {
  let {
    positionMap
  } = state

  positionMap = positionMap.slice(0)

  // DOM order and the displayed array will stay the same
  // All we have to do is swap pointers in the position map

  const temp = positionMap[firstLocation]
  positionMap[firstLocation] = positionMap[secondLocation]
  positionMap[secondLocation] = temp

  return Object.assign({}, state, {
    positionMap
  })
}

/**
 * If the specified webcast ID exists in displayedWebcasts, this function
 * replaces it with null.
 */
const removeWebcast = (state, webcastId) => {
  let {
    displayed,
    domOrder,
    positionMap,
  } = state

  displayed = displayed.slice(0)
  domOrder = domOrder.slice(0)
  positionMap = positionMap.slice(0)

  // First, find and remove it from the DOM ordering list
  let domIndex = -1;
  for (let i = 0; i < domOrder.length; i++) {
    if (domOrder[i] == webcastId) {
      domOrder[i] = null
      domIndex = i;
    }
  }

  // Remove any pointers to that DOM element from the position map
  for (let i = 0; i < positionMap.length; i++) {
    if (positionMap[i] === domIndex) {
      positionMap[i] = -1
    }
  }

  // Finally, remove the ID from the list of displayed webcasts
  let index = displayed.indexOf(webcastId)
  if (index >= 0) {
    displayed.splice(index, 1)
  }

  return Object.assign({}, state, {
    displayed,
    domOrder,
    positionMap,
  })
}

/**
 * Removes any extra webcasts when we switch to a layout with fewer available views
 */
const trimToLayout = (state) => {
  let {
    layoutId,
    displayed,
    domOrder,
    positionMap,
  } = state

  displayed = displayed.slice(0)
  domOrder = domOrder.slice(0)
  positionMap = positionMap.slice(0)

  const maxViewsForLayout = NUM_VIEWS_FOR_LAYOUT[layoutId]

  // Walk from the end of the position map, removing as many empty positions as
  // as possible until either we can't remove any more, or the array is at the
  // required size. This lets us maintain as many webcasts as possible

  for (let i = positionMap.length; i >= 0; i--) {
    if (positionMap[i] == -1) {
      positionMap.splice(i, 1)
      if (positionMap.length == maxViewsForLayout) {
        break
      }
    }
  }

  // Remove webcasts from the end, if necessary
  while (positionMap.length > maxViewsForLayout) {
    const domPosition = positionMap.pop()
    const webcastId = domOrder[domPosition]
    domOrder.splice(domPosition, 1)

    let index = displayed.indexOf(webcastId)
    if (index >= 0) {
      displayed.splice(index, 1)
    }
  }

  // Pad the end with -1s
  while (positionMap.length < MAX_SUPPORTED_VIEWS) {
    positionMap.push(-1)
  }

  // Fill in any empty spots in the dom order
  while (domOrder.length < MAX_SUPPORTED_VIEWS) {
    domOrder.push(null)
  }

  return Object.assign({}, state, {
    displayed,
    domOrder,
    positionMap,
  })
}

const videoGrid = (state = defaultState, action) => {
  switch (action.type) {
    case types.SET_LAYOUT:
      const newState = Object.assign({}, state, {
        layoutId: action.layoutId,
        layoutSet: true,
      })

      // Trim, if necessary
      return trimToLayout(newState)
    case types.ADD_WEBCAST_AT_LOCATION:
      return addWebcastAtLocation(state, action.webcastId, action.location, MAX_SUPPORTED_VIEWS)
    case types.SWAP_WEBCASTS:
      return swapWebcasts(state, action.firstLocation, action.secondLocation)
    case types.REMOVE_WEBCAST:
      return removeWebcast(state, action.webcastId)
    case types.RESET_WEBCASTS:
      return Object.assign({}, state, {
        displayedWebcasts: [],
      })
    default:
      return state
  }
}

export default videoGrid
