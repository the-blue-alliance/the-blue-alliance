import { connect } from 'react-redux'
import GamedayNavbar from '../components/GamedayNavbar'
import * as actions from '../actions'
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
    toggleChatPanelVisibility: () => dispatch(actions.toggleChatSidebarVisibility()),
    toggleHashtagPanelVisibility: () => dispatch(actions.toggleHashtagSidebarVisibility()),
    addWebcast: (id) => dispatch(actions.addWebcast(id)),
    resetWebcasts: () => dispatch(actions.resetWebcasts()),
    setLayout: (layoutId) => dispatch(actions.setLayout(layoutId))
  }
}

const GamedayNavbarContainer = connect(mapStateToProps, mapDispatchToProps)(GamedayNavbar)

export default GamedayNavbarContainer
