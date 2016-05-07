import { connect } from 'react-redux'
import ChatPanel from '../components/ChatPanel'

const mapStateToProps = (state) => {
  return {
    enabled: state.visibility.chatSidebar
  }
}

const ChatPanelContainer = connect(mapStateToProps, null)(ChatPanel)

export default ChatPanelContainer
