import { connect } from 'react-redux'
import GamedayNavbar from '../components/GamedayNavbar'
import * as actions from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  layoutId: state.layout.layoutId,
  layoutSet: state.layout.layoutSet,
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
  layoutDrawerVisible: state.visibility.layoutDrawer,
})

const mapDispatchToProps = (dispatch) => ({
  toggleChatSidebarVisibility: () => dispatch(actions.toggleChatSidebarVisibility()),
  setChatSidebarVisibility: (visible) => dispatch(actions.setChatSidebarVisibility(visible)),
  toggleHashtagSidebarVisibility: () => dispatch(actions.toggleHashtagSidebarVisibility()),
  setHashtagSidebarVisibility: (visible) => dispatch(actions.setHashtagSidebarVisibility(visible)),
  addWebcast: (id) => dispatch(actions.addWebcast(id)),
  resetWebcasts: () => dispatch(actions.resetWebcasts()),
  setLayout: (layoutId) => dispatch(actions.setLayout(layoutId)),
  toggleLayoutDrawerVisibility: () => dispatch(actions.toggleLayoutDrawerVisibility()),
  setLayoutDrawerVisibility: (visible) => dispatch(actions.setLayoutDrawerVisibility(visible)),
})

export default connect(mapStateToProps, mapDispatchToProps)(GamedayNavbar)
