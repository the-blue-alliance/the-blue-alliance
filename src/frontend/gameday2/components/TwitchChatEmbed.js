import React from "react";
import PropTypes from "prop-types";

const TwitchChatEmbed = (props) => {
  const id = `twich-chat-${props.channel}`;
  const src = `https://twitch.tv/embed/${props.channel}/chat?parent=${document.location.hostname}`;
  const style = {
    display: props.visible ? null : "none",
    width: "100%",
    height: "100%",
  };

  return (
    <div style={style}>
      <iframe
        frameBorder="0"
        scrolling="no"
        id={id}
        src={src}
        height="100%"
        width="100%"
      />
    </div>
  );
};

TwitchChatEmbed.propTypes = {
  channel: PropTypes.string.isRequired,
  visible: PropTypes.bool.isRequired,
};

export default TwitchChatEmbed;
