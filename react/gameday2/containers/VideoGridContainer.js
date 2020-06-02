import { connect } from 'react-redux'
import VideoGrid from '../components/VideoGrid'

const mapStateToProps = (state) => ({
  domOrder: state.videoGrid.domOrder,
  positionMap: state.videoGrid.positionMap,
  domOrderLivescoreOn: state.videoGrid.domOrderLivescoreOn,
  webcastsById: state.webcastsById,
  layoutId: state.videoGrid.layoutId,
})

export default connect(mapStateToProps)(VideoGrid)
