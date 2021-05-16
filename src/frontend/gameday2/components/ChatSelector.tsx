import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import ReactTransitionGroup from "react-addons-transition-group";
import { List, ListItem } from "material-ui/List";
import Paper from "material-ui/Paper";
import ActionHome from "material-ui/svg-icons/action/home";
import CheckmarkIcon from "material-ui/svg-icons/navigation/check";
import { chatPropType } from "../utils/PropTypes";
import AnimatableContainer from "./AnimatableContainer";

type Props = {
  chats: chatPropType[];
  currentChat: string;
  defaultChat: string;
  setTwitchChat: (...args: any[]) => any;
  open: boolean;
  onRequestClose: (...args: any[]) => any;
};

export default class ChatSelector extends React.Component<Props> {
  setTwitchChat(e: any, channel: any) {
    this.props.setTwitchChat(channel);
    this.props.onRequestClose();
  }

  render() {
    const chatItems: any = [];
    this.props.chats.forEach((chat) => {
      const isSelected = chat.channel === this.props.currentChat;
      const isDefault = chat.channel === this.props.defaultChat;
      const icon = isSelected ? <CheckmarkIcon /> : null;

      let chatName = chat.name;
      if (chat.channel === "firstupdatesnow" && isDefault) {
        chatName = "TBA GameDay / FUN";
      } else if (chat.channel === "firstinspires" && isDefault) {
        chatName = "TBA GameDay / FIRST";
      }

      chatItems.push(
        // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
        <ListItem
          primaryText={chatName}
          leftIcon={isDefault ? <ActionHome /> : null}
          rightIcon={icon}
          onClick={(e: any) => this.setTwitchChat(e, chat.channel)}
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
            // @ts-expect-error ts-migrate(2322) FIXME: Type '{ key: string; style: { width: string; heigh... Remove this comment to see the full error message
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
              <List onClick={(e: any) => e.stopPropagation()}>{chatItems}</List>
            </Paper>
          </AnimatableContainer>
        )}
      </ReactTransitionGroup>
    );
  }
}
