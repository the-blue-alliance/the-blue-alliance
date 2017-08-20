import { connect } from 'react-redux'
import AuthInput from '../components/AuthInput'
import { updateAuth } from '../actions'

const mapStateToProps = (state) => ({
  authId: state.auth.authId,
  authSecret: state.auth.authSecret,
  selectedEvent: state.auth.selectedEvent,
  manualEvent: state.auth.manualEvent,
})

const mapDispatchToProps = (dispatch) => ({
  setAuth: (authId, authSecret) => dispatch(updateAuth(authId, authSecret)),
})

export default connect(mapStateToProps, mapDispatchToProps)(AuthInput)
