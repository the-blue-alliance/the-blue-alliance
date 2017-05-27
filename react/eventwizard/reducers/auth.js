import { UPDATE_AUTH, CLEAR_AUTH, SET_EVENT, SET_MANUAL_EVENT } from '../constants/ActionTypes'

const defaultState = {
  selectedEvent: "",
  manualEvent: false,
}

const setNewAuth = (authId, authSecret, state) => {
  return Object.assign({}, state, {
    authId: authId,
    authSecret: authSecret
  })
}

const setNewEvent = (eventKey, state) => {
  return Object.assign({}, state, {
    selectedEvent: eventKey
  })
}

const setManualEvent = (manualEvent, state) => {
  return Object.assign({}, state, {
    manualEvent: manualEvent
  })
}

const auth = (state = defaultState, action) => {
  switch (action.type) {
    case CLEAR_AUTH:
      return setNewAuth('', '', state)
    case UPDATE_AUTH:
      return setNewAuth(action.authId, action.authSecret, state)
    case SET_EVENT:
      return setNewEvent(action.eventKey, state)
    case SET_MANUAL_EVENT:
      return setManualEvent(action.manualEvent, state)
    default:
      return state
  }
}

export default auth