import { connect } from 'react-redux'
import ChatPanel from '../components/ChatPanel'

const mapStateToProps = (state) => {
  return {
    enabled: state.visibility.chatPanel
  }
}

const ChatPanelContainer = connect(mapStateToProps, null)(ChatPanel)

export default ChatPanelContainer
