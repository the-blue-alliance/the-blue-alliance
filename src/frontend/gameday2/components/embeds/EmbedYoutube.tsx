import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";

type Props = {
  webcast: webcastPropType;
};

const EmbedYoutube = (props: Props) => {
  const src = `//www.youtube.com/embed/${props.webcast.channel}?autoplay=1`;
  return (
    <iframe
      width="100%"
      height="100%"
      src={src}
      frameBorder="0"
      allowFullScreen
    />
  );
};

export default EmbedYoutube;
