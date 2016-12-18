import { connect } from 'react-redux'
import VideoCellToolbar from '../components/VideoCellToolbar'
import { addWebcastAtPosition, swapWebcasts, removeWebcast } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = state => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = dispatch => ({
  removeWebcast: id => dispatch(removeWebcast(id)),
  addWebcastAtPosition: (webcastId, position) => dispatch(addWebcastAtPosition(webcastId, position)),
  swapWebcasts: (firstPosition, secondPosition) => dispatch(swapWebcasts(firstPosition, secondPosition)),
})

export default connect(mapStateToProps, mapDispatchToProps)(VideoCellToolbar)
