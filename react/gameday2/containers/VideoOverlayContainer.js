import { connect } from 'react-redux'
import VideoCellOverlay from '../components/VideoCellOverlay'
import { addWebcastAtLocation, swapWebcasts, removeWebcast, setLayout } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => {
  return {
    webcasts: getWebcastIdsInDisplayOrder(state),
    webcastsById: state.webcastsById,
    displayedWebcasts: state.displayedWebcasts,
    layoutId: state.layout.layoutId
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    removeWebcast: (id) => dispatch(removeWebcast(id)),
    addWebcastAtLocation: (webcastId, location) => dispatch(addWebcastAtLocation(webcastId, location)),
    swapWebcasts: (firstLocation, secondLocation) => dispatch(swapWebcasts(firstLocation, secondLocation))
  }
}

const VideoOverlayContainer = connect(mapStateToProps, mapDispatchToProps)(VideoCellOverlay)

export default VideoOverlayContainer
