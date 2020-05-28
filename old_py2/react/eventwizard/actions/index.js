import * as types from '../constants/ActionTypes'

export function setEvent(eventKey) {
  return {
    type: types.SET_EVENT,
    eventKey,
  }
}

export function clearAuth() {
  return {
    type: types.CLEAR_AUTH,
  }
}

export function updateAuth(authId, authSecret) {
  return {
    type: types.UPDATE_AUTH,
    authId,
    authSecret,
  }
}

export function setManualEvent(manualEvent) {
  return {
    type: types.SET_MANUAL_EVENT,
    manualEvent,
  }
}
