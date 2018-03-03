import { connect } from 'react-redux'
import VideoCellToolbar from '../components/VideoCellToolbar'
import { addWebcastAtPosition, swapWebcasts, removeWebcast } from '../actions'
import { getTickerMatches, getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state, props) => ({
  matches: getTickerMatches(state, props),
  favoriteTeams: state.favoriteTeams,
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  specialWebcastIds: state.specialWebcastIds,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  removeWebcast: (id) => dispatch(removeWebcast(id)),
  addWebcastAtPosition: (webcastId, position) => dispatch(addWebcastAtPosition(webcastId, position)),
  swapWebcasts: (firstPosition, secondPosition) => dispatch(swapWebcasts(firstPosition, secondPosition)),
})

export default connect(mapStateToProps, mapDispatchToProps)(VideoCellToolbar)
