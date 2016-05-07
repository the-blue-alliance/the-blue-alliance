import { connect } from 'react-redux'
import GamedayNavbar from '../components/GamedayNavbar'
import { toggleChatPanelVisibility, toggleHashtagPanelVisibility, addWebcast, resetWebcasts, setLayout } from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => {
  return {
    webcasts: getWebcastIdsInDisplayOrder(state),
    webcastsById: state.webcastsById,
    hashtagPanelVisible: state.visibility.hashtagSidebar,
    chatPanelVisible: state.visibility.chatSidebar
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    toggleChatPanelVisibility: () => dispatch(toggleChatPanelVisibility()),
    toggleHashtagPanelVisibility: () => dispatch(toggleHashtagPanelVisibility()),
    addWebcast: (id) => dispatch(addWebcast(id)),
    resetWebcasts: () => dispatch(resetWebcasts()),
    setLayout: (layoutId) => dispatch(setLayout(layoutId))
  }
}

const GamedayNavbarContainer = connect(mapStateToProps, mapDispatchToProps)(GamedayNavbar)

export default GamedayNavbarContainer
