import { connect } from 'react-redux'
import AppBar from '../components/AppBar'
import * as actions from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  layoutId: state.videoGrid.layoutId,
  layoutSet: state.videoGrid.layoutSet,
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
  layoutDrawerVisible: state.visibility.layoutDrawer,
})

const mapDispatchToProps = (dispatch) => ({
  toggleChatSidebarVisibility: () => dispatch(actions.toggleChatSidebarVisibility()),
  setChatSidebarVisibility: (visible) => dispatch(actions.setChatSidebarVisibility(visible)),
  toggleHashtagSidebarVisibility: () => dispatch(actions.toggleHashtagSidebarVisibility()),
  setHashtagSidebarVisibility: (visible) => dispatch(actions.setHashtagSidebarVisibility(visible)),
  resetWebcasts: () => dispatch(actions.resetWebcasts()),
  setLayout: (layoutId) => dispatch(actions.setLayout(layoutId)),
  toggleLayoutDrawerVisibility: () => dispatch(actions.toggleLayoutDrawerVisibility()),
  setLayoutDrawerVisibility: (visible) => dispatch(actions.setLayoutDrawerVisibility(visible)),
})

export default connect(mapStateToProps, mapDispatchToProps)(AppBar)
