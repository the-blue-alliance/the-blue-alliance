import { connect } from 'react-redux'
import GamedayNavbar from '../components/GamedayNavbar'
import { toggleChatPanelVisibility, toggleHashtagPanelVisibility } from '../actions'

const mapStateToProps = (state) => {
  return {
    webcasts: state.webcasts,
    webcastsById: state.webcastsById,
    hashtagPanelVisible: state.hashtagPanelVisible,
    chatPanelVisible: state.chatPanelVisible
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    toggleChatPanelVisibility: () => dispatch(toggleChatPanelVisibility()),
    toggleHashtagPanelVisibility: () => dispatch(toggleHashtagPanelVisibility())
  }
}

const GamedayNavbarContainer = connect(mapStateToProps, mapDispatchToProps)(GamedayNavbar)

export default GamedayNavbarContainer
