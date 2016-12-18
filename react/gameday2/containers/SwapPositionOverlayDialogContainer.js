import { connect } from 'react-redux'
import SwapPositionOverlayDialog from '../components/SwapPositionOverlayDialog'
import { swapWebcasts } from '../actions'

const mapStateToProps = (state) => ({
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  swapWebcasts: (firstPosition, secondPosition) => dispatch(swapWebcasts(firstPosition, secondPosition)),
})

export default connect(mapStateToProps, mapDispatchToProps)(SwapPositionOverlayDialog)
