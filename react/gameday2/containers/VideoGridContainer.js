import { connect } from 'react-redux'
import VideoGrid from '../components/VideoGrid'
import { addWebcastAtPosition, setLayout } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  domOrder: state.videoGrid.domOrder,
  positionMap: state.videoGrid.positionMap,
  webcastsById: state.webcastsById,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  addWebcastAtPosition: (webcastId, position) => dispatch(addWebcastAtPosition(webcastId, position)),
  setLayout: (layoutId) => dispatch(setLayout(layoutId)),
})


export default connect(mapStateToProps, mapDispatchToProps)(VideoGrid)
