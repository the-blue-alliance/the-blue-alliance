import { connect } from 'react-redux'
import SwapPositionOverlayDialog from '../components/SwapPositionOverlayDialog'
import { swapWebcasts } from '../actions'

const mapStateToProps = (state) => ({
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  swapWebcasts: (firstLocation, secondLocation) => dispatch(swapWebcasts(firstLocation, secondLocation)),
})

export default connect(mapStateToProps, mapDispatchToProps)(SwapPositionOverlayDialog)
