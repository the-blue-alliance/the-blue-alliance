/* eslint-disable react/no-danger */
import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";

type Props = {
  webcast: webcastPropType;
};

const EmbedIframe = (props: Props) => {
  const divStyle = {
    width: "100%",
    height: "100%",
  };

  let iframeMarkup = props.webcast.channel;
  iframeMarkup = iframeMarkup.replace(/&lt;/, "<");
  iframeMarkup = iframeMarkup.replace(/&gt;/, ">");
  const markup = {
    __html: iframeMarkup,
  };

  const elem = <div style={divStyle} dangerouslySetInnerHTML={markup} />;

  return elem;
};

export default EmbedIframe;
