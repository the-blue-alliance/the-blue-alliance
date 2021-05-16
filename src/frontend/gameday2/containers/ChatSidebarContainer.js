"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const actions_1 = require("../actions");
const ChatSidebar_1 = __importDefault(require("../components/ChatSidebar"));
const selectors_1 = require("../selectors");
const mapStateToProps = (state) => ({
  enabled: state.visibility.chatSidebar,
  hasBeenVisible: state.visibility.chatSidebarHasBeenVisible,
  chats: state.chats.chats,
  displayOrderChats: selectors_1.getChatsInDisplayOrder(state),
  renderedChats: state.chats.renderedChats,
  currentChat: state.chats.currentChat,
  defaultChat: state.chats.defaultChat,
});
const mapDispatchToProps = (dispatch) => ({
  setTwitchChat: (channel) => dispatch(actions_1.setTwitchChat(channel)),
  setChatSidebarVisibility: (visible) =>
    dispatch(actions_1.setChatSidebarVisibility(visible)),
  setHashtagSidebarVisibility: (visible) =>
    dispatch(actions_1.setHashtagSidebarVisibility(visible)),
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  mapDispatchToProps
)(ChatSidebar_1.default);
