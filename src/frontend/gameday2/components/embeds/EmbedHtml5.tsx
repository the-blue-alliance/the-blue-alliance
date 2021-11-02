/* global videojs */
import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";

type Props = {
  webcast: webcastPropType;
};

export default class EmbedHtml5 extends React.Component<Props> {
  componentDidMount() {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'videojs'.
    videojs(this.props.webcast.id, {
      width: "100%",
      height: "100%",
      autoplay: true,
      crossorigin: "anonymous",
    });
  }

  render() {
    return (
      <video
        controls
        id={this.props.webcast.id}
        className="video-js vjs-default-skin"
      >
        <source src={this.props.webcast.channel} type="application/x-mpegurl" />
      </video>
    );
  }
}
