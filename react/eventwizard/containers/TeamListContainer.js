import { connect } from 'react-redux'
import TeamListTab from '../components/teamsTab/TeamListTab'
import makeTrustedApiRequest from '../net/TrustedApiRequest'

const mapStateToProps = (state) => ({
  selectedEvent: state.auth.selectedEvent,
  makeTrustedRequest: (request_path, request_body, on_success, on_error) => {
    makeTrustedApiRequest(state.authId, state.authSecret, request_path, request_body, on_success, on_error)
  },
})

export default connect(mapStateToProps)(TeamListTab)
