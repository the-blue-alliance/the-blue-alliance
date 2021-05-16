import React from "react";
import EmbedUstream from "./embeds/EmbedUstream";
import EmbedYoutube from "./embeds/EmbedYoutube";
import EmbedTwitch from "./embeds/EmbedTwitch";
import EmbedLivestream from "./embeds/EmbedLivestream";
import EmbedIframe from "./embeds/EmbedIframe";
import EmbedHtml5 from "./embeds/EmbedHtml5";
import EmbedDacast from "./embeds/EmbedDacast";
import EmbedDirectLink from "./embeds/EmbedDirectLink";
import EmbedRtmp from "./embeds/EmbedRtmp";
import EmbedNotSupported from "./embeds/EmbedNotSupported";
import { webcastPropType } from "../utils/webcastUtils";

type Props = {
  webcast?: webcastPropType;
};

export default class WebcastEmbed extends React.Component<Props> {
  render() {
    let cellEmbed;
    // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
    switch (this.props.webcast.type) {
      case "ustream":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedUstream webcast={this.props.webcast} />;
        break;
      case "youtube":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedYoutube webcast={this.props.webcast} />;
        break;
      case "twitch":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedTwitch webcast={this.props.webcast} />;
        break;
      case "livestream":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedLivestream webcast={this.props.webcast} />;
        break;
      case "iframe":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedIframe webcast={this.props.webcast} />;
        break;
      case "html5":
        // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
        cellEmbed = <EmbedHtml5 webcast={this.props.webcast} />;
        break;
      case "dacast":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedDacast webcast={this.props.webcast} />;
        break;
      case "direct_link":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = <EmbedDirectLink webcast={this.props.webcast} />;
        break;
      case "rtmp":
        // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
        cellEmbed = <EmbedRtmp webcast={this.props.webcast} />;
        break;
      default:
        cellEmbed = <EmbedNotSupported />;
        break;
    }

    return cellEmbed;
  }
}
