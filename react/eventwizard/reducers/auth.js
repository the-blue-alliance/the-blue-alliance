import { UPDATE_AUTH, CLEAR_AUTH, SET_EVENT, SET_MANUAL_EVENT } from '../constants/ActionTypes'

const defaultState = {
  selectedEvent: '',
  manualEvent: false,
}

const setNewAuth = (authId, authSecret, state) => (
  Object.assign({}, state, {
    authId,
    authSecret,
  })
)

const setNewEvent = (eventKey, state) => (
  Object.assign({}, state, {
    selectedEvent: eventKey,
  })
)

const setManualEvent = (manualEvent, state) => (
  Object.assign({}, state, {
    manualEvent,
  })
)

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
