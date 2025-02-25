import React from "react";
import PropTypes from "prop-types";
import ReactTransitionGroup from "react-transition-group/TransitionGroup";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import Paper from "@mui/material/Paper";
import HomeIcon from '@mui/icons-material/Home';
import CheckIcon from '@mui/icons-material/Check';
import { chatPropType } from "../utils/PropTypes";
import AnimatableContainer from "./AnimatableContainer";

export default class ChatSelector extends React.Component {
  static propTypes = {
    chats: PropTypes.arrayOf(chatPropType).isRequired,
    currentChat: PropTypes.string.isRequired,
    defaultChat: PropTypes.string.isRequired,
    setTwitchChat: PropTypes.func.isRequired,
    open: PropTypes.bool.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  };

  setTwitchChat(e, channel) {
    this.props.setTwitchChat(channel);
    this.props.onRequestClose();
  }

  render() {
    const chatItems = [];
    this.props.chats.forEach((chat) => {
      const isSelected = chat.channel === this.props.currentChat;
      const isDefault = chat.channel === this.props.defaultChat;
      const icon = isSelected ? <CheckIcon/> : null;

      let chatName = chat.name;
      if (chat.channel === "firstupdatesnow" && isDefault) {
        chatName = "TBA GameDay / FUN";
      } else if (chat.channel === "firstinspires" && isDefault) {
        chatName = "TBA GameDay / FIRST";
      }

      chatItems.push(
        <ListItem
          primaryText={chatName}
          leftIcon={isDefault ? <HomeIcon/> : null}
          rightIcon={icon}
          onClick={(e) => this.setTwitchChat(e, chat.channel)}
          key={chat.channel}
        />
      );
    });

    const overlayStyle = {
      width: "100%",
      height: "100%",
      background: "rgba(0,0,0,0.2)",
      position: "absolute",
      transition: "all 150ms ease-in",
      willChange: "opacity",
    };

    const listStyle = {
      width: "100%",
      position: "absolute",
      bottom: 0,
      transition: "all 150ms ease-in",
      willChange: "transform opacity",
      height: "90%",
      overflowY: "auto",
    };

    return (
      <ReactTransitionGroup component="div">
        {this.props.open && (
          <AnimatableContainer
            key="overlay"
            style={overlayStyle}
            onClick={() => this.props.onRequestClose()}
            beginStyle={{
              opacity: 0,
            }}
            endStyle={{
              opacity: 1,
            }}
          />
        )}
        {this.props.open && (
          <AnimatableContainer
            key="selector"
            style={listStyle}
            beginStyle={{
              opacity: 0,
              transform: "translate(0, 50%)",
            }}
            endStyle={{
              opacity: 1,
              transform: "translate(0, 0)",
            }}
          >
            <Paper zDepth={4}>
              <List onClick={(e) => e.stopPropagation()}>{chatItems}</List>
            </Paper>
          </AnimatableContainer>
        )}
      </ReactTransitionGroup>
    );
  }
}
