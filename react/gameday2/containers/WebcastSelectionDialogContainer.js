import { connect } from 'react-redux'
import WebcastSelectionDialog from '../components/WebcastSelectionDialog'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  specialWebcastIds: state.specialWebcastIds,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
})

export default connect(mapStateToProps)(WebcastSelectionDialog)
