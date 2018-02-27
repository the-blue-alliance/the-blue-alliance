import { connect } from 'react-redux'
import VideoCell from '../components/VideoCell'
import { addWebcastAtPosition, setLayout, swapWebcasts, togglePositionLivescore } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  addWebcastAtPosition: (webcastId, position) => dispatch(addWebcastAtPosition(webcastId, position)),
  setLayout: (layoutId) => dispatch(setLayout(layoutId)),
  swapWebcasts: (firstPosition, secondPosition) => dispatch(swapWebcasts(firstPosition, secondPosition)),
  togglePositionLivescore: (position) => dispatch(togglePositionLivescore(position)),
})

export default connect(mapStateToProps, mapDispatchToProps)(VideoCell)
