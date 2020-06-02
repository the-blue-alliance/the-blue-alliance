import { connect } from 'react-redux'
import EventSelector from '../components/EventSelector'
import { setEvent, setManualEvent, clearAuth } from '../actions'

const mapStateToProps = (state) => ({
  selectedEvent: state.auth.selectedEvent,
  manualEvent: state.auth.manualEvent,
})

const mapDispatchToProps = (dispatch) => ({
  setEvent: (eventKey) => dispatch(setEvent(eventKey)),
  setManualEvent: (manualEvent) => dispatch(setManualEvent(manualEvent)),
  clearAuth: () => dispatch(clearAuth()),
})

export default connect(mapStateToProps, mapDispatchToProps)(EventSelector)
