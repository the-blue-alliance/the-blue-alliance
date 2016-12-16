import { connect } from 'react-redux'
import WebcastSelectionOverlayDialog from '../components/WebcastSelectionOverlayDialog'
import { addWebcastAtLocation, swapWebcasts, removeWebcast } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  removeWebcast: (id) => dispatch(removeWebcast(id)),
  addWebcastAtLocation: (webcastId, location) => dispatch(addWebcastAtLocation(webcastId, location)),
  swapWebcasts: (firstLocation, secondLocation) => dispatch(swapWebcasts(firstLocation, secondLocation)),
})

export default connect(mapStateToProps, mapDispatchToProps)(WebcastSelectionOverlayDialog)
