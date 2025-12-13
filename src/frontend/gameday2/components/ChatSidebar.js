import React from "react";
import PropTypes from "prop-types";
import { useTheme } from "@mui/material/styles";
import IconButton from "@mui/material/IconButton";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import Toolbar from "@mui/material/Toolbar";
const white = "#fff";
import ChatAnalyticsTracker from "./ChatAnalyticsTracker";
import TwitchChatEmbed from "./TwitchChatEmbed";
import ChatSelector from "./ChatSelector";
import { chatPropType } from "../utils/PropTypes";

const ChatSidebar = (props) => {
  const theme = useTheme();
  const [chatSelectorOpen, setChatSelectorOpen] = React.useState(false);

  React.useEffect(() => {
    function onResize() {
      if (window.innerWidth < 760) {
        props.setChatSidebarVisibility(false);
        props.setHashtagSidebarVisibility(false);
      }
    }
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [props]);
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
    display: props.enabled ? null : "none",
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
    background:
      (theme.palette && theme.palette.primary && theme.palette.primary.main) ||
      undefined,
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
  props.renderedChats.forEach((chat) => {
    const visible = chat === props.currentChat;
    renderedChats.push(
      <TwitchChatEmbed channel={chat} key={chat} visible={visible} />
    );
  });

  const currentChat = props.chats[props.currentChat];
  let currentChatName = "UNKNOWN";
  if (currentChat) {
    currentChatName = `${currentChat.name} Chat`;
    if (
      currentChat.channel === "firstupdatesnow" &&
      props.defaultChat === "firstupdatesnow"
    ) {
      currentChatName = "TBA GameDay / FUN";
    } else if (
      currentChat.channel === "firstinspires" &&
      props.defaultChat === "firstinspires"
    ) {
      currentChatName = "TBA GameDay / FIRST";
    }
  }

  let content;
  if (props.hasBeenVisible) {
    content = (
      <div style={panelContainerStyle}>
        <div style={chatEmbedContainerStyle}>{renderedChats}</div>
        <Toolbar
          style={switcherToolbarStyle}
          onClick={() => setChatSelectorOpen(true)}
        >
          <div>
            <div style={toolbarTitleStyle}>{currentChatName}</div>
          </div>
          <div>
            <IconButton style={toolbarButtonStyle}>
              <ArrowDropUpIcon style={toolbarButtonIconStyle} />
            </IconButton>
          </div>
        </Toolbar>
        <ChatSelector
          chats={props.displayOrderChats}
          currentChat={props.currentChat}
          defaultChat={props.defaultChat}
          setTwitchChat={props.setTwitchChat}
          open={chatSelectorOpen}
          onRequestClose={() => setChatSelectorOpen(false)}
        />
        {props.enabled && (
          <ChatAnalyticsTracker currentChat={props.currentChat} />
        )}
      </div>
    );
  } else {
    content = <div />;
  }

  return content;
};

ChatSidebar.propTypes = {
  enabled: PropTypes.bool.isRequired,
  hasBeenVisible: PropTypes.bool.isRequired,
  chats: PropTypes.objectOf(chatPropType).isRequired,
  displayOrderChats: PropTypes.arrayOf(chatPropType).isRequired,
  renderedChats: PropTypes.arrayOf(PropTypes.string).isRequired,
  currentChat: PropTypes.string.isRequired,
  defaultChat: PropTypes.string.isRequired,
  setTwitchChat: PropTypes.func.isRequired,
  setChatSidebarVisibility: PropTypes.func.isRequired,
  setHashtagSidebarVisibility: PropTypes.func.isRequired,
};

export default ChatSidebar;
