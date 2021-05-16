import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import muiThemeable from "material-ui/styles/muiThemeable";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import IconButton from "material-ui/IconButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import ArrowDropUp from "material-ui/svg-icons/navigation/arrow-drop-up";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { Toolbar, ToolbarGroup, ToolbarTitle } from "material-ui/Toolbar";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { white } from "material-ui/styles/colors";
import ChatAnalyticsTracker from "./ChatAnalyticsTracker";
import TwitchChatEmbed from "./TwitchChatEmbed";
import ChatSelector from "./ChatSelector";
import { chatPropType } from "../utils/PropTypes";

type Props = {
  enabled: boolean;
  hasBeenVisible: boolean;
  chats: {
    [key: string]: chatPropType;
  };
  displayOrderChats: chatPropType[];
  renderedChats: string[];
  currentChat: string;
  defaultChat: string;
  setTwitchChat: (...args: any[]) => any;
  muiTheme: any;
  setChatSidebarVisibility: any;
  setHashtagSidebarVisibility: any;
};

type State = any;

class ChatSidebar extends React.Component<Props, State> {
  constructor(props: Props) {
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
      color: white,
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

    const renderedChats: any = [];
    this.props.renderedChats.forEach((chat) => {
      const visible = chat === this.props.currentChat;
      renderedChats.push(
        <TwitchChatEmbed channel={chat} key={chat} visible={visible} />
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
      content = (
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ position: string; top: any; right: number;... Remove this comment to see the full error message
        <div style={panelContainerStyle}>
          {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ position: string; top: number; bottom: num... Remove this comment to see the full error message */}
          <div style={chatEmbedContainerStyle}>{renderedChats}</div>
          <Toolbar
            style={switcherToolbarStyle}
            onClick={() => this.onRequestOpenChatSelector()}
          >
            <ToolbarGroup>
              <ToolbarTitle text={currentChatName} style={toolbarTitleStyle} />
            </ToolbarGroup>
            <ToolbarGroup lastChild>
              <IconButton
                style={toolbarButtonStyle}
                iconStyle={toolbarButtonIconStyle}
              >
                <ArrowDropUp color={white} />
              </IconButton>
            </ToolbarGroup>
          </Toolbar>
          <ChatSelector
            chats={this.props.displayOrderChats}
            currentChat={this.props.currentChat}
            defaultChat={this.props.defaultChat}
            setTwitchChat={this.props.setTwitchChat}
            open={this.state.chatSelectorOpen}
            onRequestClose={() => this.onRequestCloseChatSelector()}
          />
          {this.props.enabled && (
            <ChatAnalyticsTracker currentChat={this.props.currentChat} />
          )}
        </div>
      );
    } else {
      content = <div />;
    }

    return content;
  }
}

export default muiThemeable()(ChatSidebar);
