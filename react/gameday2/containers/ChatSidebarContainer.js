import { connect } from 'react-redux'
import ChatSidebar from '../components/ChatSidebar'

const mapStateToProps = state => ({
  enabled: state.visibility.chatSidebar,
  hasBeenVisible: state.visibility.chatSidebarHasBeenVisible,
})

export default connect(mapStateToProps, null)(ChatSidebar)
