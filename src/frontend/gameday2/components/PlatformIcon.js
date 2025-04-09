import React from "react";
import PropTypes from "prop-types";
import YouTubeIcon from "./icons/YouTubeIcon";
import TwitchIcon from "./icons/TwitchIcon";

export default class PlatformIcon extends React.Component {
  static propTypes = {
    platform: PropTypes.string.isRequired,
  };

  static iconStyle = {
    position: "absolute",
    top: 0,
    left: "5px",
    margin: "12px",
  };

  render() {
    if (this.props.platform === "youtube")
      return <YouTubeIcon style={iconStyle} />;
    if (this.props.platform === "twitch")
      return <TwitchIcon style={iconStyle} />;
    return <></>; // If we don't have a logo for this platform, leave an empty space
  }
}
