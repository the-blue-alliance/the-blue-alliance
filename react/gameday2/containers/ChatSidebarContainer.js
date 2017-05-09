import { connect } from 'react-redux'
import { setTwitchChat, setChatSidebarVisibility } from '../actions'
import ChatSidebar from '../components/ChatSidebar'
import { getChatsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  enabled: state.visibility.chatSidebar,
  hasBeenVisible: state.visibility.chatSidebarHasBeenVisible,
  chats: state.chats.chats,
  displayOrderChats: getChatsInDisplayOrder(state),
  renderedChats: state.chats.renderedChats,
  currentChat: state.chats.currentChat,
})

const mapDispatchToProps = (dispatch) => ({
  setTwitchChat: (channel) => dispatch(setTwitchChat(channel)),
  setChatSidebarVisibility: (visible) => dispatch(setChatSidebarVisibility(visible)),
})

export default connect(mapStateToProps, mapDispatchToProps)(ChatSidebar)
