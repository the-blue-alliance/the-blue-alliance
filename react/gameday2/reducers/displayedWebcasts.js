import { ADD_WEBCAST, REMOVE_WEBCAST, RESET_WEBCASTS } from '../actions'

const displayedWebcasts = (state = [], action) => {
  switch(action.type) {
    case ADD_WEBCAST:
    return state.concat(action.id)
    case REMOVE_WEBCAST:
    return state.filter((id) => id != action.id)
    case RESET_WEBCASTS:
    return []
    default:
    return state
  }
}

export default displayedWebcasts
