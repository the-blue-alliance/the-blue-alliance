import { connect } from 'react-redux'
import GamedayNavbar from '../components/GamedayNavbar'
import { toggleChatPanelVisibility, toggleHashtagPanelVisibility, addWebcast, resetWebcasts } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => {
  return {
    webcasts: getWebcastIdsInDisplayOrder(state),
    webcastsById: state.webcastsById,
    hashtagPanelVisible: state.hashtagPanelVisible,
    chatPanelVisible: state.chatPanelVisible
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    toggleChatPanelVisibility: () => dispatch(toggleChatPanelVisibility()),
    toggleHashtagPanelVisibility: () => dispatch(toggleHashtagPanelVisibility()),
    addWebcast: (id) => dispatch(addWebcast(id)),
    resetWebcasts: () => dispatch(resetWebcasts())
  }
}

const GamedayNavbarContainer = connect(mapStateToProps, mapDispatchToProps)(GamedayNavbar)

export default GamedayNavbarContainer
