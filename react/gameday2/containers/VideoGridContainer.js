import { connect } from 'react-redux'
import VideoGrid from '../components/VideoGrid'
import { addWebcastAtLocation, setLayout } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  displayedWebcasts: state.displayedWebcasts,
  layoutId: state.layout.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  addWebcastAtLocation: (webcastId, location) => dispatch(addWebcastAtLocation(webcastId, location)),
  setLayout: (layoutId) => dispatch(setLayout(layoutId)),
})


export default connect(mapStateToProps, mapDispatchToProps)(VideoGrid)
