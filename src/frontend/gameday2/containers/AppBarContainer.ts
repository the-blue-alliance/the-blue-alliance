import { connect } from "react-redux";
import AppBar from "../components/AppBar";
import * as actions from "../actions";
import { getWebcastIdsInDisplayOrder } from "../selectors";

const mapStateToProps = (state: any) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  layoutId: state.videoGrid.layoutId,
  layoutSet: state.videoGrid.layoutSet,
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
  layoutDrawerVisible: state.visibility.layoutDrawer,
});

const mapDispatchToProps = (dispatch: any) => ({
  toggleChatSidebarVisibility: () =>
    dispatch(actions.toggleChatSidebarVisibility()),

  setChatSidebarVisibility: (visible: any) =>
    dispatch(actions.setChatSidebarVisibility(visible)),

  toggleHashtagSidebarVisibility: () =>
    dispatch(actions.toggleHashtagSidebarVisibility()),

  setHashtagSidebarVisibility: (visible: any) =>
    dispatch(actions.setHashtagSidebarVisibility(visible)),
  resetWebcasts: () => dispatch(actions.resetWebcasts()),
  setLayout: (layoutId: any) => dispatch(actions.setLayout(layoutId)),

  toggleLayoutDrawerVisibility: () =>
    dispatch(actions.toggleLayoutDrawerVisibility()),

  setLayoutDrawerVisibility: (visible: any) =>
    dispatch(actions.setLayoutDrawerVisibility(visible)),
});

export default connect(mapStateToProps, mapDispatchToProps)(AppBar);
