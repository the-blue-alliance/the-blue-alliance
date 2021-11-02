import { connect } from "react-redux";
import {
  setTwitchChat,
  setChatSidebarVisibility,
  setHashtagSidebarVisibility,
} from "../actions";
import ChatSidebar from "../components/ChatSidebar";
import { getChatsInDisplayOrder } from "../selectors";

const mapStateToProps = (state: any) => ({
  enabled: state.visibility.chatSidebar,
  hasBeenVisible: state.visibility.chatSidebarHasBeenVisible,
  chats: state.chats.chats,
  displayOrderChats: getChatsInDisplayOrder(state),
  renderedChats: state.chats.renderedChats,
  currentChat: state.chats.currentChat,
  defaultChat: state.chats.defaultChat,
});

const mapDispatchToProps = (dispatch: any) => ({
  setTwitchChat: (channel: any) => dispatch(setTwitchChat(channel)),
  setChatSidebarVisibility: (visible: any) =>
    dispatch(setChatSidebarVisibility(visible)),
  setHashtagSidebarVisibility: (visible: any) =>
    dispatch(setHashtagSidebarVisibility(visible)),
});

export default connect(mapStateToProps, mapDispatchToProps)(ChatSidebar);
