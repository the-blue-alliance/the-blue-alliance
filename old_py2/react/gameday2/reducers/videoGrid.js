import * as types from '../constants/ActionTypes'
import { MAX_SUPPORTED_VIEWS, NUM_VIEWS_FOR_LAYOUT } from '../constants/LayoutConstants'

// Position map maps from a position index in the grid to a position in the DOM ordering

const defaultPositionMap = new Array(MAX_SUPPORTED_VIEWS)
const defaultDomOrder = new Array(MAX_SUPPORTED_VIEWS)
const defaultDomOrderLivescoreOn = new Array(MAX_SUPPORTED_VIEWS)
defaultDomOrder.fill(null)
defaultPositionMap.fill(-1)
defaultDomOrderLivescoreOn.fill(null)

const defaultState = {
  layoutId: 0,
  layoutSet: false,
  displayed: [],
  domOrder: defaultDomOrder,
  positionMap: defaultPositionMap,
  domOrderLivescoreOn: defaultDomOrderLivescoreOn,
}

/**
 * Removes any extra webcasts when we switch to a layout with fewer available views
 */
const trimToLayout = (state) => {
  let {
    displayed,
    domOrder,
    positionMap,
    domOrderLivescoreOn,
  } = state

  const layoutId = state.layoutId

  displayed = displayed.slice(0)
  domOrder = domOrder.slice(0)
  positionMap = positionMap.slice(0)
  domOrderLivescoreOn = domOrderLivescoreOn.slice(0)

  const maxViewsForLayout = NUM_VIEWS_FOR_LAYOUT[layoutId]

  // Walk from the end of the position map, removing as many empty positions as
  // as possible until either we can't remove any more, or the array is at the
  // required size. This lets us maintain as many webcasts as possible

  for (let i = positionMap.length; i >= 0; i--) {
    if (positionMap.length === maxViewsForLayout) {
      break
    }
    if (positionMap[i] === -1) {
      positionMap.splice(i, 1)
    }
  }

  // Remove webcasts from the end, if necessary
  while (positionMap.length > maxViewsForLayout) {
    const domPosition = positionMap.pop()
    const webcastId = domOrder[domPosition]
    domOrder[domPosition] = null
    domOrderLivescoreOn[domPosition] = null

    const index = displayed.indexOf(webcastId)
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
    domOrderLivescoreOn.push(null)
  }

  return Object.assign({}, state, {
    displayed,
    domOrder,
    positionMap,
    domOrderLivescoreOn,
  })
}

const addWebcastAtPosition = (state, webcastId, position, maxSupportedViews) => {
  if (!state.layoutSet || position >= NUM_VIEWS_FOR_LAYOUT[state.layoutId]) {
    return state
  }

  if (position < 0 || position >= maxSupportedViews) {
    return state
  }

  let {
    displayed,
    domOrder,
    positionMap,
    domOrderLivescoreOn,
  } = state

  displayed = displayed.slice(0)
  domOrder = domOrder.slice(0)
  positionMap = positionMap.slice(0)
  domOrderLivescoreOn = domOrderLivescoreOn.slice(0)

  // See if there's already a webcast at this position
  const existingIndex = positionMap[position]
  if (existingIndex >= 0) {
    // There's already a webcast at this position with a corresponding DOM element
    const oldId = domOrder[existingIndex]
    domOrder[existingIndex] = webcastId

    // Update the displayed array
    const displayedIndex = displayed.indexOf(oldId)
    if (displayedIndex >= 0) {
      displayed[displayedIndex] = webcastId
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
        positionMap[position] = i
        domOrderLivescoreOn[i] = false
        break
      }
    }

    displayed.push(webcastId)
  }

  return trimToLayout(Object.assign({}, state, {
    displayed,
    domOrder,
    positionMap,
    domOrderLivescoreOn,
  }))
}

const swapWebcasts = (state, firstPosition, secondPosition) => {
  let {
    positionMap,
  } = state

  positionMap = positionMap.slice(0)

  // DOM order and the displayed array will stay the same
  // All we have to do is swap pointers in the position map

  const temp = positionMap[firstPosition]
  positionMap[firstPosition] = positionMap[secondPosition]
  positionMap[secondPosition] = temp

  return Object.assign({}, state, {
    positionMap,
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
    domOrderLivescoreOn,
  } = state

  displayed = displayed.slice(0)
  domOrder = domOrder.slice(0)
  positionMap = positionMap.slice(0)
  domOrderLivescoreOn = domOrderLivescoreOn.slice(0)

  // First, find and remove it from the DOM ordering list
  let domIndex = -1
  for (let i = 0; i < domOrder.length; i++) {
    if (domOrder[i] === webcastId) {
      domOrder[i] = null
      domOrderLivescoreOn[i] = null
      domIndex = i
    }
  }

  // Remove any pointers to that DOM element from the position map
  for (let i = 0; i < positionMap.length; i++) {
    if (positionMap[i] === domIndex) {
      positionMap[i] = -1
    }
  }

  // Finally, remove the ID from the list of displayed webcasts
  const index = displayed.indexOf(webcastId)
  if (index >= 0) {
    displayed.splice(index, 1)
  }

  return Object.assign({}, state, {
    displayed,
    domOrder,
    positionMap,
    domOrderLivescoreOn,
  })
}

const toggleLivescore = (state, position) => {
  let {
    domOrderLivescoreOn,
  } = state

  domOrderLivescoreOn = domOrderLivescoreOn.slice(0)

  // Toggle livescore at position
  const index = state.positionMap[position]
  domOrderLivescoreOn[index] = !domOrderLivescoreOn[index]

  return Object.assign({}, state, {
    domOrderLivescoreOn,
  })
}

const videoGrid = (state = defaultState, action) => {
  switch (action.type) {
    case types.SET_LAYOUT: {
      const newState = Object.assign({}, state, {
        layoutId: action.layoutId,
        layoutSet: true,
      })

      // Trim, if necessary
      return trimToLayout(newState)
    }
    case types.ADD_WEBCAST_AT_POSITION:
      return addWebcastAtPosition(state, action.webcastId, action.position, MAX_SUPPORTED_VIEWS)
    case types.SWAP_WEBCASTS:
      return swapWebcasts(state, action.firstPosition, action.secondPosition)
    case types.REMOVE_WEBCAST:
      return removeWebcast(state, action.webcastId)
    case types.RESET_WEBCASTS:
      return Object.assign({}, state, {
        displayed: [],
        domOrder: defaultDomOrder,
        positionMap: defaultPositionMap,
      })
    case types.TOGGLE_POSITION_LIVESCORE:
      return toggleLivescore(state, action.position)
    default:
      return state
  }
}

export default videoGrid
