import { connect } from 'react-redux'
import VideoGridUpdated from '../components/VideoGridUpdated'
import { addWebcastAtLocation, setLayout } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  domOrder: state.videoGrid.domOrder,
  positionMap: state.videoGrid.positionMap,
  webcastsById: state.webcastsById,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.layout.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  addWebcastAtLocation: (webcastId, location) => dispatch(addWebcastAtLocation(webcastId, location)),
  setLayout: (layoutId) => dispatch(setLayout(layoutId)),
})


export default connect(mapStateToProps, mapDispatchToProps)(VideoGridUpdated)
