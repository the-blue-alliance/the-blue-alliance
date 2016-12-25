import { connect } from 'react-redux'
import ChatSidebar from '../components/ChatSidebar'

const mapStateToProps = (state) => ({
  enabled: state.visibility.chatSidebar,
  hasBeenVisible: state.visibility.chatSidebarHasBeenVisible,
  chats: state.chats.chats,
  renderedChats: state.chats.renderedChats,
  currentChat: state.chats.currentChat,
})

const mapDispatchToProps = (dispatch) => ({
  setTwitchChat: (channel) => dispatch(actions.setTwitchChat(channel)),
})

export default connect(mapStateToProps, mapDispatchToProps)(ChatSidebar)
