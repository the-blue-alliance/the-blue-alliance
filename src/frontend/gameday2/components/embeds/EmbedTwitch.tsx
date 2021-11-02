import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";

type Props = {
  webcast: webcastPropType;
};

const EmbedTwitch = (props: Props) => {
  const channel = props.webcast.channel;
  const iframeSrc = `https://player.twitch.tv/?channel=${channel}&parent=${document.location.hostname}`;
  return (
    <iframe
      src={iframeSrc}
      frameBorder="0"
      scrolling="no"
      height="100%"
      width="100%"
      allowFullScreen
    />
  );
};

export default EmbedTwitch;
