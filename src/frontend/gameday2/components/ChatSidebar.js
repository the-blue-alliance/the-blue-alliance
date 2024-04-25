import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import { IconButton, Toolbar } from "@mui/material";
import white from "@mui/material/colors/common";
import { useTheme } from "@mui/material/styles";
import PropTypes from "prop-types";
import React from "react";
import { chatPropType } from "../utils/PropTypes";
import ChatAnalyticsTracker from "./ChatAnalyticsTracker";
import ChatSelector from "./ChatSelector";
import TwitchChatEmbed from "./TwitchChatEmbed";

class ChatSidebar extends React.Component {
  static propTypes = {
    enabled: PropTypes.bool.isRequired,
    hasBeenVisible: PropTypes.bool.isRequired,
    chats: PropTypes.objectOf(chatPropType).isRequired,
    displayOrderChats: PropTypes.arrayOf(chatPropType).isRequired,
    renderedChats: PropTypes.arrayOf(PropTypes.string).isRequired,
    currentChat: PropTypes.string.isRequired,
    defaultChat: PropTypes.string.isRequired,
    setTwitchChat: PropTypes.func.isRequired,
    muiTheme: PropTypes.object.isRequired,
    setChatSidebarVisibility: PropTypes.object.isRequired,
    setHashtagSidebarVisibility: PropTypes.object.isRequired,
  };

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
    const theme = useTheme();

    const metrics = {
      switcherHeight: 36,
    };

    const panelContainerStyle = {
      position: "absolute",
      top: theme.layout.appBarHeight,
      right: 0,
      bottom: 0,
      width: theme.layout.chatPanelWidth,
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
      background: theme.palette.primary1Color,
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

    const renderedChats = [];
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

    let content = <div />;

    if (this.props.hasBeenVisible) {
      content = (
        <div style={panelContainerStyle}>
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
                <ArrowDropUpIcon color={white} />
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
    }

    return content;
  }
}

export default ChatSidebar;
