import { connect } from 'react-redux'
import SwapPositionDialog from '../components/SwapPositionDialog'
import { swapWebcasts } from '../actions'

const mapStateToProps = (state) => ({
  layoutId: state.videoGrid.layoutId,
})

const mapDispatchToProps = (dispatch) => ({
  swapWebcasts: (firstPosition, secondPosition) => dispatch(swapWebcasts(firstPosition, secondPosition)),
})

export default connect(mapStateToProps, mapDispatchToProps)(SwapPositionDialog)
