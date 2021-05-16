"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const muiThemeable_1 = __importDefault(
  require("material-ui/styles/muiThemeable")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const IconButton_1 = __importDefault(require("material-ui/IconButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const arrow_drop_up_1 = __importDefault(
  require("material-ui/svg-icons/navigation/arrow-drop-up")
);
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const Toolbar_1 = require("material-ui/Toolbar");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const colors_1 = require("material-ui/styles/colors");
const ChatAnalyticsTracker_1 = __importDefault(
  require("./ChatAnalyticsTracker")
);
const TwitchChatEmbed_1 = __importDefault(require("./TwitchChatEmbed"));
const ChatSelector_1 = __importDefault(require("./ChatSelector"));
class ChatSidebar extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.state = {
      chatSelectorOpen: false,
    };
    this.onResize = this.onResize.bind(this);
  }
  componentDidMount() {
    this.onResize();
    window.addEventListener("resize", this.onResize);
  }
  onResize() {
    if (window.innerWidth < 760) {
      this.props.setChatSidebarVisibility(false);
      this.props.setHashtagSidebarVisibility(false);
    }
  }
  onRequestOpenChatSelector() {
    this.setState({
      chatSelectorOpen: true,
    });
  }
  onRequestCloseChatSelector() {
    this.setState({
      chatSelectorOpen: false,
    });
  }
  render() {
    const metrics = {
      switcherHeight: 36,
    };
    const panelContainerStyle = {
      position: "absolute",
      top: this.props.muiTheme.layout.appBarHeight,
      right: 0,
      bottom: 0,
      width: this.props.muiTheme.layout.chatPanelWidth,
      background: "#EFEEF1",
      display: this.props.enabled ? null : "none",
      zIndex: 1000,
    };
    const chatEmbedContainerStyle = {
      position: "absolute",
      top: 0,
      bottom: metrics.switcherHeight,
      width: "100%",
    };
    const switcherToolbarStyle = {
      position: "absolute",
      bottom: 0,
      height: metrics.switcherHeight,
      width: "100%",
      background: this.props.muiTheme.palette.primary1Color,
      cursor: "pointer",
    };
    const toolbarTitleStyle = {
      color: colors_1.white,
      fontSize: 16,
    };
    const toolbarButtonStyle = {
      width: metrics.switcherHeight,
      height: metrics.switcherHeight,
      padding: 8,
    };
    const toolbarButtonIconStyle = {
      width: metrics.switcherHeight - 16,
      height: metrics.switcherHeight - 16,
    };
    const renderedChats = [];
    this.props.renderedChats.forEach((chat) => {
      const visible = chat === this.props.currentChat;
      renderedChats.push(
        jsx_runtime_1.jsx(
          TwitchChatEmbed_1.default,
          { channel: chat, visible: visible },
          chat
        )
      );
    });
    const currentChat = this.props.chats[this.props.currentChat];
    let currentChatName = "UNKNOWN";
    if (currentChat) {
      currentChatName = `${currentChat.name} Chat`;
      if (
        currentChat.channel === "firstupdatesnow" &&
        this.props.defaultChat === "firstupdatesnow"
      ) {
        currentChatName = "TBA GameDay / FUN";
      } else if (
        currentChat.channel === "firstinspires" &&
        this.props.defaultChat === "firstinspires"
      ) {
        currentChatName = "TBA GameDay / FIRST";
      }
    }
    let content;
    if (this.props.hasBeenVisible) {
      content =
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ position: string; top: any; right: number;... Remove this comment to see the full error message
        jsx_runtime_1.jsxs(
          "div",
          Object.assign(
            { style: panelContainerStyle },
            {
              children: [
                jsx_runtime_1.jsx(
                  "div",
                  Object.assign(
                    { style: chatEmbedContainerStyle },
                    { children: renderedChats }
                  ),
                  void 0
                ),
                jsx_runtime_1.jsxs(
                  Toolbar_1.Toolbar,
                  Object.assign(
                    {
                      style: switcherToolbarStyle,
                      onClick: () => this.onRequestOpenChatSelector(),
                    },
                    {
                      children: [
                        jsx_runtime_1.jsx(
                          Toolbar_1.ToolbarGroup,
                          {
                            children: jsx_runtime_1.jsx(
                              Toolbar_1.ToolbarTitle,
                              {
                                text: currentChatName,
                                style: toolbarTitleStyle,
                              },
                              void 0
                            ),
                          },
                          void 0
                        ),
                        jsx_runtime_1.jsx(
                          Toolbar_1.ToolbarGroup,
                          Object.assign(
                            { lastChild: true },
                            {
                              children: jsx_runtime_1.jsx(
                                IconButton_1.default,
                                Object.assign(
                                  {
                                    style: toolbarButtonStyle,
                                    iconStyle: toolbarButtonIconStyle,
                                  },
                                  {
                                    children: jsx_runtime_1.jsx(
                                      arrow_drop_up_1.default,
                                      { color: colors_1.white },
                                      void 0
                                    ),
                                  }
                                ),
                                void 0
                              ),
                            }
                          ),
                          void 0
                        ),
                      ],
                    }
                  ),
                  void 0
                ),
                jsx_runtime_1.jsx(
                  ChatSelector_1.default,
                  {
                    chats: this.props.displayOrderChats,
                    currentChat: this.props.currentChat,
                    defaultChat: this.props.defaultChat,
                    setTwitchChat: this.props.setTwitchChat,
                    open: this.state.chatSelectorOpen,
                    onRequestClose: () => this.onRequestCloseChatSelector(),
                  },
                  void 0
                ),
                this.props.enabled &&
                  jsx_runtime_1.jsx(
                    ChatAnalyticsTracker_1.default,
                    { currentChat: this.props.currentChat },
                    void 0
                  ),
              ],
            }
          ),
          void 0
        );
    } else {
      content = jsx_runtime_1.jsx("div", {}, void 0);
    }
    return content;
  }
}
exports.default = muiThemeable_1.default()(ChatSidebar);
