import { connect } from 'react-redux'
import GamedayNavbarMaterial from '../components/GamedayNavbarMaterial'
import * as actions from '../actions'
import { getWebcastIdsInDisplayOrder } from '../selectors'

const mapStateToProps = (state) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
})

const mapDispatchToProps = (dispatch) => ({
  toggleChatSidebarVisibility: () => dispatch(actions.toggleChatSidebarVisibility()),
  toggleHashtagSidebarVisibility: () => dispatch(actions.toggleHashtagSidebarVisibility()),
  addWebcast: (id) => dispatch(actions.addWebcast(id)),
  resetWebcasts: () => dispatch(actions.resetWebcasts()),
  setLayout: (layoutId) => dispatch(actions.setLayout(layoutId)),
})

export default connect(mapStateToProps, mapDispatchToProps)(GamedayNavbarMaterial)
