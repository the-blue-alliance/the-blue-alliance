import { connect } from 'react-redux'
import ChatSidebar from '../components/ChatSidebar'

const mapStateToProps = (state) => {
  return {
    enabled: state.visibility.chatSidebar
  }
}

const ChatSidebarContainer = connect(mapStateToProps, null)(ChatSidebar)

export default ChatSidebarContainer
