import { connect } from 'react-redux'
import TeamListTab from '../components/TeamListTab'

const mapStateToProps = (state) => ({
  selectedEvent: state.auth.selectedEvent,
})

export default connect(mapStateToProps)(TeamListTab)
