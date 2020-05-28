import { connect } from 'react-redux'
import AuthTools from '../components/AuthTools'
import { updateAuth } from '../actions'

const mapStateToProps = (state) => ({
  authId: state.auth.authId,
  authSecret: state.auth.authSecret,
  manualEvent: state.auth.manualEvent,
  selectedEvent: state.auth.selectedEvent,
})

const mapDispatchToProps = (dispatch) => ({
  setAuth: (authId, authSecret) => dispatch(updateAuth(authId, authSecret)),
})

export default connect(mapStateToProps, mapDispatchToProps)(AuthTools)
